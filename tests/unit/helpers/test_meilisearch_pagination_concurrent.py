"""Tests de la pagination concurrente (ordre, exhaustivité, non-mutation)."""

from __future__ import annotations

import pytest

from ffbb_data_client.helpers.meilisearch_client_extension import (
    MeilisearchClientExtension,
)
from ffbb_data_client.models.multi_search_query import MultiSearchQuery
from ffbb_data_client.models.multi_search_result_competitions import (
    CompetitionsMultiSearchResult,
)
from ffbb_data_client.models.multi_search_results_class import MultiSearchResults


class _ConcurrentFake(MeilisearchClientExtension):
    """Simule Meilisearch : renvoie ``limit`` hits à partir de ``offset`` et
    annonce un total fixe, comme le ferait le moteur (maxTotalHits = 1000)."""

    TOTAL = 2500  # -> 3 pages (1000 + 1000 + 500)

    def __init__(self) -> None:
        super().__init__(bearer_token="fake", url="http://fake")
        self.call_order: list[int] = []

    def smart_multi_search(self, queries, cached_session=None):
        batch_results = []
        for q in queries:
            offset = q.offset or 0
            limit = q.limit or 0
            self.call_order.append(offset)
            hits = [{"id": f"hit_{offset + i}"} for i in range(limit)]
            res = CompetitionsMultiSearchResult()
            res.hits = hits
            res.estimated_total_hits = self.TOTAL
            batch_results.append(res)
        # Tri pour simuler un retour désordonné (la fusion doit réordonner).
        return MultiSearchResults(results=batch_results)

    async def smart_multi_search_async(self, queries, cached_session=None):
        return self.smart_multi_search(queries, cached_session)


def test_concurrent_pagination_sync_collects_all_hits_in_order():
    client = _ConcurrentFake()
    query = MultiSearchQuery(index_uid="competitions", limit=20, offset=0)

    result = client.recursive_smart_multi_search([query])

    assert result is not None
    assert result.results is not None
    hits = result.results[0].hits
    assert len(hits) == _ConcurrentFake.TOTAL
    ids = [h["id"] for h in hits]
    assert ids == [f"hit_{i}" for i in range(_ConcurrentFake.TOTAL)]
    # La requête d'origine du caller reste intacte.
    assert query.offset == 0
    assert query.limit == 20


@pytest.mark.asyncio
async def test_concurrent_pagination_async_collects_all_hits_in_order():
    client = _ConcurrentFake()
    query = MultiSearchQuery(index_uid="competitions", limit=20, offset=0)

    result = await client.recursive_smart_multi_search_async([query])

    assert result is not None
    assert result.results is not None
    hits = result.results[0].hits
    assert len(hits) == _ConcurrentFake.TOTAL
    ids = [h["id"] for h in hits]
    assert ids == [f"hit_{i}" for i in range(_ConcurrentFake.TOTAL)]
    assert query.offset == 0
    assert query.limit == 20
