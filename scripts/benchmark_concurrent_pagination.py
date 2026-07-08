"""Benchmark de la pagination concurrente vs séquentielle (correcte).

Ne touche pas à l'API réelle : on simule Meilisearch en injectant une latence
réseau par appel ``multi_search`` et en plafonnant les hits à 1000/page
(comme le ``maxTotalHits`` de Meilisearch).

On isole deux effets :
  1. Correction : l'ancien algo séquentiel tronquait à 1000 hits (il demandait
     tout le reste en un seul appel, mais Meili ne renvoie que 1000).
  2. Concurrence : on compare un parcours SÉQUENTIEL *correct* (même logique de
     découpe, exécution une page après l'autre) au parcours CONCURRENT du SDK.

Usage : rtk python scripts/benchmark_concurrent_pagination.py
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

from ffbb_data_client import SearchSpec
from ffbb_data_client.clients._search_facade import (
    _SearchFacade,
    _dispatch_search_async,
    search_many_async,
)
from ffbb_data_client.helpers.meilisearch_client_extension import (
    MeilisearchClientExtension,
    _build_pagination_jobs,
)
from ffbb_data_client.models.multi_search_query import MultiSearchQuery
from ffbb_data_client.models.multi_search_results_class import MultiSearchResults

logging.disable(logging.INFO)  # silence les logs d'init du SDK

LATENCY = 0.05  # RTT simulé par appel multi_search (secondes)
TOTAL_HITS = 25_000  # redéfini par scénario
MEILI_PAGE_CAP = 1000  # maxTotalHits réaliste


@dataclass
class _FakeResult:
    hits: list = field(default_factory=list)
    estimated_total_hits: int | None = None


class _BenchClient(MeilisearchClientExtension):
    """Client simulé : chaque multi_search dort LATENCY puis renvoie les hits
    restants (bornés à MEILI_PAGE_CAP par page)."""

    def __init__(self) -> None:
        super().__init__(bearer_token="x", url="http://x")

    async def smart_multi_search_async(
        self, queries, cached_session=None
    ) -> MultiSearchResults:
        await asyncio.sleep(LATENCY)
        out = []
        for q in queries:
            offset = q.offset or 0
            limit = q.limit or 0
            remaining = max(0, TOTAL_HITS - offset)
            n = min(limit, remaining, MEILI_PAGE_CAP)
            out.append(
                _FakeResult(
                    hits=[{"id": offset + i} for i in range(n)],
                    estimated_total_hits=TOTAL_HITS,
                )
            )
        return MultiSearchResults(results=out)


def _total_hits(result: MultiSearchResults | None) -> int:
    if not result or not result.results:
        return 0
    return sum(len(r.hits or []) for r in result.results)


async def correct_sequential(client: _BenchClient, queries: list[MultiSearchQuery]):
    """Parcours SÉQUENTIEL mais *correct* : même découpe de pages que le SDK,
    exécution une page après l'autre (sans asyncio.gather)."""
    result = await client.smart_multi_search_async(queries)
    if not result or not queries or not result.results:
        return result
    jobs = _build_pagination_jobs(queries, result)
    batches = [jobs[s : s + 10] for s in range(0, len(jobs), 10)]
    for batch in batches:
        batch_queries = [pq for _, _, pq in batch]
        new = await client.smart_multi_search_async(batch_queries)
        if new and new.results:
            for k, (orig_idx, _offset, _q) in enumerate(batch):
                t = result.results[orig_idx]
                src = new.results[k]
                if src.hits and t.hits is not None:
                    t.hits.extend(src.hits)
    return result


async def _time(coro_factory, repeats: int = 5):
    await coro_factory()  # warm-up
    best = float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        r = await coro_factory()
        best = min(best, time.perf_counter() - t0)
    return best, _total_hits(r)


async def run_scenario(nb_queries: int, total: int):
    global TOTAL_HITS
    TOTAL_HITS = total

    seq_t, seq_hits = await _time(
        lambda: correct_sequential(
            _BenchClient(),
            [
                MultiSearchQuery(index_uid="c", limit=10, offset=0)
                for _ in range(nb_queries)
            ],
        )
    )
    con_t, con_hits = await _time(
        lambda: _BenchClient().recursive_smart_multi_search_async(
            [
                MultiSearchQuery(index_uid="c", limit=10, offset=0)
                for _ in range(nb_queries)
            ]
        )
    )
    speedup = seq_t / con_t if con_t > 0 else float("inf")
    return {
        "q": nb_queries,
        "total": total,
        "pages": (total - 10 + MEILI_PAGE_CAP - 1) // MEILI_PAGE_CAP,
        "seq_t": seq_t,
        "con_t": con_t,
        "seq_hits": seq_hits,
        "con_hits": con_hits,
        "speedup": speedup,
    }


class _BenchSearchClient(_BenchClient):
    """Facade simulée héritant de ``_BenchClient`` : chaque ``smart_multi_search_async``
    dort ``LATENCY`` puis renvoie des hits bornés à ``MEILI_PAGE_CAP`` (comportement
    hérité tel quel). On expose ``search_many_async`` / ``search_multiple_organismes_async``
    en pointant ``_meilisearch`` sur l'instance elle-même.
    """

    def __init__(self) -> None:
        super().__init__()
        self._meilisearch = self

    search_many_async = search_many_async
    _dispatch_search_async = _dispatch_search_async
    search_multiple_organismes_async = _SearchFacade.search_multiple_organismes_async


def _total_many_hits(results) -> int:
    if not results:
        return 0
    total = 0
    for res in results:
        if not res:
            continue
        for item in res:
            hits = getattr(item, "hits", None)
            if hits:
                total += len(hits)
    return total


async def _sequential_search_many(client: _BenchSearchClient, specs: list) -> int:
    total = 0
    for spec in specs:
        # Même charge par recherche que le chemin concurrent (spec.limit) pour
        # une comparaison équitable ; on reste sur une seule page (pas de
        # pagination) afin d'isoler l'effet de concurrence.
        res = await client.search_multiple_organismes_async(
            [spec.name], limit=spec.limit
        )
        total += _total_many_hits([res])
    return total


async def _bench(coro_factory, repeats: int = 5):
    await coro_factory()  # warm-up
    best = float("inf")
    last = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        r = await coro_factory()
        best = min(best, time.perf_counter() - t0)
        last = r
    return best, last


async def run_search_many_scenario(nb_searches: int, total: int):
    global TOTAL_HITS
    # Chaque recherche indépendante tient sur une seule page (hits bornés à
    # MEILI_PAGE_CAP) : aucune pagination, donc un seul aller-retour réseau
    # simulé par recherche. Cela isole proprement l'effet de concurrence.
    TOTAL_HITS = min(total, MEILI_PAGE_CAP)

    specs = [
        SearchSpec(resource="organismes", name=f"q{i}", limit=MEILI_PAGE_CAP)
        for i in range(nb_searches)
    ]

    seq_t, _ = await _bench(
        lambda: _sequential_search_many(_BenchSearchClient(), specs)
    )
    con_t, con_r = await _bench(lambda: _BenchSearchClient().search_many_async(specs))
    speedup = seq_t / con_t if con_t > 0 else float("inf")
    return {
        "nb_searches": nb_searches,
        "seq_t": seq_t,
        "con_t": con_t,
        "speedup": speedup,
        "total_hits": _total_many_hits(con_r),
    }


async def main() -> None:
    print(
        f"Benchmark — latence simulée {LATENCY * 1000:.0f} ms/appel, "
        f"plafond Meili {MEILI_PAGE_CAP} hits/page\n"
    )
    print(
        f"{'Requêtes':>8} {'Total':>8} {'Pages':>6} "
        f"{'Séquentiel':>12} {'Concurrent':>12} {'Speedup':>8}  Hits(s/c)"
    )
    print("-" * 78)
    for nb_q, total in [
        (1, 2_500),
        (1, 25_000),
        (5, 25_000),
        (10, 25_000),
        (10, 50_000),
        (20, 50_000),
    ]:
        r = await run_scenario(nb_q, total)
        print(
            f"{r['q']:>8} {r['total']:>8} {r['pages']:>6} "
            f"{r['seq_t'] * 1000:>10.0f} ms {r['con_t'] * 1000:>10.0f} ms "
            f"{r['speedup']:>7.1f}x  {r['seq_hits']}/{r['con_hits']}"
        )

    print()
    print("search_many_async (recherches indépendantes)")
    print(
        f"{'Recherches':>10} {'Séquentiel':>12} {'Concurrent':>12} {'Speedup':>8}  Hits"
    )
    print("-" * 56)
    for nb in [1, 5, 10, 20]:
        r = await run_search_many_scenario(nb, 25_000)
        print(
            f"{r['nb_searches']:>10} {r['seq_t'] * 1000:>10.0f} ms "
            f"{r['con_t'] * 1000:>10.0f} ms {r['speedup']:>7.1f}x  {r['total_hits']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
