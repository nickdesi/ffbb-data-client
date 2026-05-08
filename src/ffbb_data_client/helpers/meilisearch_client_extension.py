from __future__ import annotations

from collections.abc import Sequence

import httpx
from httpx import Client

from ..clients.meilisearch_client import MeilisearchClient
from ..models.multi_search_query import MultiSearchQuery
from ..models.multi_search_results_class import MultiSearchResults


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
        results = self.multi_search(queries, cached_session)

        # Should filter results.hits according to query.q
        if queries and results and results.results:
            results.results = [
                query.filter_result(res) if query.q else res
                for query, res in zip(queries, results.results, strict=True)
            ]

        return results

    async def smart_multi_search_async(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> MultiSearchResults | None:
        results = await self.multi_search_async(queries, cached_session)

        # Should filter results.hits according to query.q
        if queries and results and results.results:
            results.results = [
                query.filter_result(res) if query.q else res
                for query, res in zip(queries, results.results, strict=True)
            ]

        return results

    def recursive_smart_multi_search(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: Client | None = None,
    ) -> MultiSearchResults | None:
        result = self.smart_multi_search(queries, cached_session)
        if not result or not queries or not result.results:
            return result

        MAX_ITERATIONS = 20
        for _ in range(MAX_ITERATIONS):
            next_queries: list[MultiSearchQuery] = []
            query_indices: list[int] = []

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

            if not next_queries:
                break

            new_result = self.smart_multi_search(next_queries, cached_session)

            if new_result and new_result.results:
                for orig_idx, query_result in zip(
                    query_indices, new_result.results, strict=True
                ):
                    orig_result = result.results[orig_idx]
                    hits_list = orig_result.hits
                    if query_result.hits and hits_list is not None:
                        hits_list.extend(query_result.hits)
            else:
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

        # Iterative pagination: collect all remaining queries per iteration
        # and fetch them in a single multi_search call, repeating until done.
        MAX_ITERATIONS = 20
        for _ in range(MAX_ITERATIONS):
            next_queries: list[MultiSearchQuery] = []
            query_indices: list[int] = []

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

            if not next_queries:
                break

            new_result = await self.smart_multi_search_async(
                next_queries, cached_session
            )

            if new_result and new_result.results:
                for orig_idx, query_result in zip(
                    query_indices, new_result.results, strict=True
                ):
                    orig_result = result.results[orig_idx]
                    hits_list = orig_result.hits
                    if query_result.hits and hits_list is not None:
                        hits_list.extend(query_result.hits)
            else:
                break

        return result

    def recursive_multi_search(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: Client | None = None,
    ) -> MultiSearchResults | None:
        """Alias for recursive_smart_multi_search for backward compatibility."""
        return self.recursive_smart_multi_search(queries, cached_session)
