from __future__ import annotations

from collections.abc import Sequence

import httpx
from httpx import Client

from ..clients.meilisearch_client import MeilisearchClient
from ..models.multi_search_query import MultiSearchQuery
from ..models.multi_search_results_class import MultiSearchResults

_MAX_PAGINATION_ITERATIONS = 20


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


def _collect_next_pagination_queries(
    queries: Sequence[MultiSearchQuery],
    result: MultiSearchResults,
) -> tuple[list[MultiSearchQuery], list[int]]:
    """Calcule les requêtes de pagination restantes et leurs indices."""
    next_queries: list[MultiSearchQuery] = []
    query_indices: list[int] = []
    if not result.results:
        return next_queries, query_indices

    for i, (querie, query_result) in enumerate(
        zip(queries, result.results, strict=True)
    ):
        nb_hits = len(query_result.hits) if query_result.hits else 0
        querie_offset = querie.offset or 0
        querie_limit = querie.limit or 10

        if query_result.estimated_total_hits is not None and nb_hits < (
            query_result.estimated_total_hits - querie_offset
        ):
            querie.offset = querie_offset + querie_limit
            querie.limit = query_result.estimated_total_hits - nb_hits
            next_queries.append(querie)
            query_indices.append(i)

    return next_queries, query_indices


def _merge_pagination_hits(
    result: MultiSearchResults,
    query_indices: list[int],
    new_result: MultiSearchResults | None,
) -> bool:
    """Fusionne les hits paginés dans result. Retourne True si la boucle
    doit continuer, False si elle doit s'arrêter."""
    if not (new_result and new_result.results):
        return False
    target_results = result.results
    if target_results is None:
        return False
    for orig_idx, query_result in zip(query_indices, new_result.results, strict=True):
        orig_result = target_results[orig_idx]
        hits_list = orig_result.hits
        if query_result.hits and hits_list is not None:
            hits_list.extend(query_result.hits)
    return True


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

    def recursive_smart_multi_search(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: Client | None = None,
    ) -> MultiSearchResults | None:
        result = self.smart_multi_search(queries, cached_session)
        if not result or not queries or not result.results:
            return result

        for _ in range(_MAX_PAGINATION_ITERATIONS):
            next_queries, query_indices = _collect_next_pagination_queries(
                queries, result
            )
            if not next_queries:
                break
            new_result = self.smart_multi_search(next_queries, cached_session)
            if not _merge_pagination_hits(result, query_indices, new_result):
                break

        return result

    async def recursive_smart_multi_search_async(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> MultiSearchResults | None:
        result = await self.smart_multi_search_async(queries, cached_session)
        if not result or not queries or not result.results:
            return result

        # Pagination itérative : on collecte les requêtes restantes par itération
        # et on les récupère en un seul multi_search, jusqu'à épuisement.
        for _ in range(_MAX_PAGINATION_ITERATIONS):
            next_queries, query_indices = _collect_next_pagination_queries(
                queries, result
            )
            if not next_queries:
                break
            new_result = await self.smart_multi_search_async(
                next_queries, cached_session
            )
            if not _merge_pagination_hits(result, query_indices, new_result):
                break

        return result

    def recursive_multi_search(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: Client | None = None,
    ) -> MultiSearchResults | None:
        """Alias for recursive_smart_multi_search for backward compatibility."""
        return self.recursive_smart_multi_search(queries, cached_session)
