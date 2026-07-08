from __future__ import annotations

import asyncio
import copy
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor

import httpx
from httpx import Client

from ..clients.meilisearch_client import MeilisearchClient
from ..models.multi_search_query import MultiSearchQuery
from ..models.multi_search_results_class import MultiSearchResults

# Meilisearch plafonne le nombre de hits renvoyés par requête (maxTotalHits,
# défaut 1000). On découpe la pagination en pages de cette taille pour pouvoir
# les exécuter en parallèle au lieu d'enchaîner les allers-retours réseau.
_PAGE_SIZE_CAP = 1000

# Nombre maximal de sous-requêtes par appel multi_search (reste sous la limite
# par défaut de Meilisearch) et borne la concurrence globale.
_BATCH_SIZE = 10


def _apply_query_filters(
    queries: Sequence[MultiSearchQuery] | None,
    results: MultiSearchResults | None,
) -> MultiSearchResults | None:
    """Filtre results.hits selon query.q (logique partagée sync/async)."""
    if queries and results and results.results:
        result_list = results.results
        results.results = [
            query.filter_result(res) if query.q else res
            for query, res in zip(queries, result_list, strict=True)
        ]
    return results


def _build_pagination_jobs(
    queries: Sequence[MultiSearchQuery],
    result: MultiSearchResults,
) -> list[tuple[int, int, MultiSearchQuery]]:
    """Construit les pages de pagination restantes (requêtes clonées, non mutées).

    Renvoie une liste de ``(index_original, offset, requête_clonée)``. Chaque
    page est découpée à ``_PAGE_SIZE_CAP`` pour respecter la limite Meilisearch
    et peut être exécutée indépendamment des autres.
    """
    jobs: list[tuple[int, int, MultiSearchQuery]] = []
    if not result.results:
        return jobs

    for i, (query, query_result) in enumerate(
        zip(queries, result.results, strict=True)
    ):
        if query_result.hits is None:
            continue
        estimated = query_result.estimated_total_hits
        if estimated is None:
            continue

        initial_offset = query.offset or 0
        already = len(query_result.hits)
        ceiling = (
            estimated  # on récupère tout le jeu de résultats (sémantique historique)
        )
        offset = initial_offset + already
        while offset < ceiling:
            take = min(_PAGE_SIZE_CAP, ceiling - offset)
            # copy superficielle (pas de __init__) : les sous-classes de
            # MultiSearchQuery (ex. OrganismesMultiSearchQuery) ont un __init__
            # restrictif, donc dataclasses.replace échouerait ici.
            page_query = copy.copy(query)
            page_query.offset = offset
            page_query.limit = take
            jobs.append((i, offset, page_query))
            offset += take

    return jobs


def _single_result(multi: MultiSearchResults, index: int) -> MultiSearchResults:
    """Isole le i-ème sous-résultat d'un multi_search dans un MultiSearchResults
    à un élément, pour une fusion cohérente avec ``_merge_page``."""
    assert multi.results is not None
    return MultiSearchResults(results=[multi.results[index]])


def _merge_page(
    result: MultiSearchResults,
    orig_idx: int,
    page_result: MultiSearchResults | None,
) -> None:
    """Fusionne les hits d'une page dans le résultat original (par index)."""
    if result.results is None or page_result is None or page_result.results is None:
        return
    target = result.results[orig_idx]
    src = page_result.results[0]
    if src.hits and target.hits is not None:
        target.hits.extend(src.hits)


class MeilisearchClientExtension(MeilisearchClient):
    def __init__(
        self,
        bearer_token: str,
        url: str,
        debug: bool = False,
        cached_session: Client | None = None,
        *,
        async_cached_session: httpx.AsyncClient | None = None,
    ):
        super().__init__(
            bearer_token,
            url,
            debug,
            cached_session,
            async_cached_session=async_cached_session,
        )

    def smart_multi_search(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: Client | None = None,
    ) -> MultiSearchResults | None:
        return _apply_query_filters(queries, self.multi_search(queries, cached_session))

    async def smart_multi_search_async(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> MultiSearchResults | None:
        return _apply_query_filters(
            queries, await self.multi_search_async(queries, cached_session)
        )

    def _fetch_batch_sync(
        self,
        batch: list[tuple[int, int, MultiSearchQuery]],
        cached_session: Client | None,
    ) -> list[tuple[int, int, MultiSearchResults | None]]:
        """Exécute un lot de pages dans un seul multi_search et associe chaque
        résultat à son index/offset d'origine."""
        batch_queries = [pq for _, _, pq in batch]
        new_result = self.smart_multi_search(batch_queries, cached_session)
        out: list[tuple[int, int, MultiSearchResults | None]] = []
        if new_result and new_result.results:
            for k, (orig_idx, offset, _q) in enumerate(batch):
                out.append((orig_idx, offset, _single_result(new_result, k)))
        return out

    async def _fetch_batch_async(
        self,
        batch: list[tuple[int, int, MultiSearchQuery]],
        cached_session: httpx.AsyncClient | None,
    ) -> list[tuple[int, int, MultiSearchResults | None]]:
        """Variante asynchrone de ``_fetch_batch_sync``."""
        batch_queries = [pq for _, _, pq in batch]
        new_result = await self.smart_multi_search_async(batch_queries, cached_session)
        out: list[tuple[int, int, MultiSearchResults | None]] = []
        if new_result and new_result.results:
            for k, (orig_idx, offset, _q) in enumerate(batch):
                out.append((orig_idx, offset, _single_result(new_result, k)))
        return out

    def recursive_smart_multi_search(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: Client | None = None,
    ) -> MultiSearchResults | None:
        result = self.smart_multi_search(queries, cached_session)
        if not result or not queries or not result.results:
            return result

        jobs = _build_pagination_jobs(queries, result)
        if not jobs:
            return result

        # Découpe en lots et exécution concurrente (pool de threads) pour
        # réduire la latence réseau cumulée de la pagination.
        batches = [jobs[s : s + _BATCH_SIZE] for s in range(0, len(jobs), _BATCH_SIZE)]
        workers = min(8, len(batches))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            pages = [
                page
                for batch_pages in executor.map(
                    self._fetch_batch_sync, batches, [cached_session] * len(batches)
                )
                for page in batch_pages
            ]

        pages.sort(key=lambda x: (x[0], x[1]))
        for orig_idx, _offset, page_result in pages:
            _merge_page(result, orig_idx, page_result)

        return result

    async def recursive_smart_multi_search_async(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> MultiSearchResults | None:
        result = await self.smart_multi_search_async(queries, cached_session)
        if not result or not queries or not result.results:
            return result

        jobs = _build_pagination_jobs(queries, result)
        if not jobs:
            return result

        batches = [jobs[s : s + _BATCH_SIZE] for s in range(0, len(jobs), _BATCH_SIZE)]
        # asyncio.gather exécute tous les lots en parallèle (bound par _BATCH_SIZE).
        gathered = await asyncio.gather(
            *(self._fetch_batch_async(batch, cached_session) for batch in batches)
        )
        pages = [page for batch_pages in gathered for page in batch_pages]

        pages.sort(key=lambda x: (x[0], x[1]))
        for orig_idx, _offset, page_result in pages:
            _merge_page(result, orig_idx, page_result)

        return result

    def recursive_multi_search(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: Client | None = None,
    ) -> MultiSearchResults | None:
        """Alias for recursive_smart_multi_search for backward compatibility."""
        return self.recursive_smart_multi_search(queries, cached_session)
