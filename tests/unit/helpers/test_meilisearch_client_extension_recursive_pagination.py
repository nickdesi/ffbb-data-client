from ffbb_data_client.helpers.meilisearch_client_extension import (
    MeilisearchClientExtension,
)
from ffbb_data_client.models.multi_search_query import MultiSearchQuery
from ffbb_data_client.models.multi_search_result_competitions import (
    CompetitionsMultiSearchResult,
)
from ffbb_data_client.models.multi_search_results_class import MultiSearchResults


class FakeMeilisearchClient(MeilisearchClientExtension):
    def __init__(self):
        super().__init__(bearer_token="fake", url="http://fake")
        self.call_count = 0

    def smart_multi_search(self, queries, cached_session=None):
        self.call_count += 1

        # First call: initial results
        if self.call_count == 1:
            res1 = CompetitionsMultiSearchResult()
            res1.hits = [{"id": "hit_1_1"}]
            res1.estimated_total_hits = 1  # No pagination needed for q1

            res2 = CompetitionsMultiSearchResult()
            res2.hits = [{"id": "hit_2_1"}]
            res2.estimated_total_hits = 2  # Pagination needed for q2

            res3 = CompetitionsMultiSearchResult()
            res3.hits = [{"id": "hit_3_1"}]
            res3.estimated_total_hits = 1  # No pagination needed for q3

            return MultiSearchResults(results=[res1, res2, res3])

        # Second call: paginated results
        if self.call_count == 2:
            res_paginated = CompetitionsMultiSearchResult()
            res_paginated.hits = [{"id": "hit_2_2"}]
            res_paginated.estimated_total_hits = 2

            # Note: The extension recursive loop will pass a list with 1 query
            return MultiSearchResults(results=[res_paginated])

        return MultiSearchResults(results=[])


def test_recursive_smart_multi_search_subset_pagination():
    client = FakeMeilisearchClient()

    q1 = MultiSearchQuery(index_uid="competitions", limit=1)
    q2 = MultiSearchQuery(index_uid="competitions", limit=1)
    q3 = MultiSearchQuery(index_uid="competitions", limit=1)

    queries = [q1, q2, q3]

    result = client.recursive_smart_multi_search(queries)

    assert result is not None
    assert len(result.results) == 3

    # Query 1 shouldn't have extra hits
    assert len(result.results[0].hits) == 1
    assert result.results[0].hits[0]["id"] == "hit_1_1"

    # Query 2 should have the paginated hit correctly appended
    assert len(result.results[1].hits) == 2
    assert result.results[1].hits[0]["id"] == "hit_2_1"
    assert result.results[1].hits[1]["id"] == "hit_2_2"

    # Query 3 shouldn't have extra hits (crucial check for the bug)
    assert len(result.results[2].hits) == 1
    assert result.results[2].hits[0]["id"] == "hit_3_1"

    assert client.call_count == 2


def test_merge_page_with_empty_or_missing_results():
    from ffbb_data_client.helpers.meilisearch_client_extension import _merge_page

    res = MultiSearchResults(results=[CompetitionsMultiSearchResult()])
    res.results[0].hits = [{"id": "hit1"}]

    # 1. page_result with empty results list (was crashing with IndexError: list index out of range)
    empty_page = MultiSearchResults(results=[])
    _merge_page(res, 0, empty_page)
    assert len(res.results[0].hits) == 1

    # 2. page_result is None
    _merge_page(res, 0, None)
    assert len(res.results[0].hits) == 1

    # 3. orig_idx out of bounds
    _merge_page(res, 999, empty_page)
