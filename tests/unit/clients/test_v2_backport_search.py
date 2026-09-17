"""Tests for v2 backport: search_engagements, search_formations, filter_by, sort."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from ffbb_data_client.clients.api_ffbb_app_client import ApiFFBBAppClient
from ffbb_data_client.clients.ffbb_data_client import FFBBDataClient
from ffbb_data_client.clients.meilisearch_ffbb_client import MeilisearchFFBBClient
from ffbb_data_client.models.multi_search_result_competitions import (
    CompetitionsMultiSearchResult,
)
from ffbb_data_client.models.multi_search_result_engagements import (
    EngagementsMultiSearchResult,
)
from ffbb_data_client.models.multi_search_result_formations import (
    FormationsMultiSearchResult,
)
from ffbb_data_client.models.multi_search_result_organismes import (
    OrganismesMultiSearchResult,
)
from ffbb_data_client.models.multi_search_results_class import MultiSearchResults


class TestV2BackportSearch(unittest.TestCase):
    """Tests for new search_engagements/formations + filter/sort params."""

    def setUp(self) -> None:
        with patch("ffbb_data_client.clients.meilisearch_client.CacheManager"):
            api_client = MagicMock(spec=ApiFFBBAppClient)
            api_client.cached_session = None
            api_client.async_cached_session = None
            meilisearch_client = MeilisearchFFBBClient(bearer_token="test-token")
            self.client = FFBBDataClient(api_client, meilisearch_client)

    def _make_mock_results(self, result_mock: MagicMock) -> MultiSearchResults:
        results = MagicMock(spec=MultiSearchResults)
        results.results = [result_mock]
        return results

    # -- search_engagements ----------------------------------------------

    @patch.object(MeilisearchFFBBClient, "recursive_smart_multi_search")
    def test_search_engagements(self, mock_rms: MagicMock) -> None:
        mock_result = MagicMock(spec=EngagementsMultiSearchResult)
        mock_result.hits = [MagicMock(nom="Clermont")]
        mock_rms.return_value = self._make_mock_results(mock_result)

        result = self.client.search_engagements("Clermont")
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "hits"))

    @patch.object(MeilisearchFFBBClient, "recursive_smart_multi_search")
    def test_search_multiple_engagements(self, mock_rms: MagicMock) -> None:
        mock_result = MagicMock(spec=EngagementsMultiSearchResult)
        mock_rms.return_value = self._make_mock_results(mock_result)
        result = self.client.search_multiple_engagements(["Clermont"])
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)  # type: ignore[arg-type]

    # -- search_formations -----------------------------------------------

    @patch.object(MeilisearchFFBBClient, "recursive_smart_multi_search")
    def test_search_formations(self, mock_rms: MagicMock) -> None:
        mock_result = MagicMock(spec=FormationsMultiSearchResult)
        mock_result.hits = [MagicMock(title="Coach Formation")]
        mock_rms.return_value = self._make_mock_results(mock_result)

        result = self.client.search_formations("coach")
        self.assertIsNotNone(result)

    @patch.object(MeilisearchFFBBClient, "recursive_smart_multi_search")
    def test_search_multiple_formations(self, mock_rms: MagicMock) -> None:
        mock_result = MagicMock(spec=FormationsMultiSearchResult)
        mock_rms.return_value = self._make_mock_results(mock_result)
        result = self.client.search_multiple_formations(["coach"])
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)  # type: ignore[arg-type]

    # -- filter_by / sort params -----------------------------------------

    @patch.object(MeilisearchFFBBClient, "recursive_smart_multi_search")
    def test_search_with_filter(self, mock_rms: MagicMock) -> None:
        mock_result = MagicMock(spec=OrganismesMultiSearchResult)
        mock_result.hits = [MagicMock(), MagicMock(), MagicMock()]
        mock_rms.return_value = self._make_mock_results(mock_result)

        result = self.client.search_organismes(
            "Clermont",
            filter=['codePostal = "63000"'],
            limit=5,
        )
        self.assertIsNotNone(result)
        # Verify filter and limit were passed through to the query
        mock_rms.assert_called_once()
        queries = mock_rms.call_args[0][0]
        self.assertEqual(queries[0].filter, ['codePostal = "63000"'])

    @patch.object(MeilisearchFFBBClient, "recursive_smart_multi_search")
    def test_search_with_sort(self, mock_rms: MagicMock) -> None:
        mock_result = MagicMock(spec=CompetitionsMultiSearchResult)
        mock_rms.return_value = self._make_mock_results(mock_result)

        result = self.client.search_competitions(
            "championnat",
            sort=["libelle:asc"],
            limit=10,
        )
        self.assertIsNotNone(result)
        mock_rms.assert_called_once()
        queries = mock_rms.call_args[0][0]
        self.assertEqual(queries[0].sort, ["libelle:asc"])

    @patch.object(MeilisearchFFBBClient, "recursive_smart_multi_search")
    def test_search_with_limit(self, mock_rms: MagicMock) -> None:
        mock_result = MagicMock(spec=OrganismesMultiSearchResult)
        mock_rms.return_value = self._make_mock_results(mock_result)

        result = self.client.search_organismes("Paris", limit=3)
        self.assertIsNotNone(result)
        mock_rms.assert_called_once()
        queries = mock_rms.call_args[0][0]
        self.assertEqual(queries[0].limit, 3)


class TestV2BackportSearchAsync(unittest.IsolatedAsyncioTestCase):
    """Async tests for search_*_async filter/sort/limit parameters."""

    async def asyncSetUp(self) -> None:
        with patch("ffbb_data_client.clients.meilisearch_client.CacheManager"):
            api_client = MagicMock(spec=ApiFFBBAppClient)
            api_client.cached_session = None
            api_client.async_cached_session = None
            meilisearch_client = MeilisearchFFBBClient(bearer_token="test-token")
            self.client = FFBBDataClient(api_client, meilisearch_client)

    def _make_mock_results(self, result_mock: MagicMock) -> MultiSearchResults:
        results = MagicMock(spec=MultiSearchResults)
        results.results = [result_mock]
        return results

    @patch.object(MeilisearchFFBBClient, "recursive_smart_multi_search_async")
    async def test_search_organismes_async_with_limit_and_filter(
        self, mock_rms_async: MagicMock
    ) -> None:
        mock_result = MagicMock(spec=OrganismesMultiSearchResult)
        mock_rms_async.return_value = self._make_mock_results(mock_result)

        result = await self.client.search_organismes_async(
            "Clermont",
            filter=['codePostal = "63000"'],
            sort=["nom:asc"],
            limit=5,
        )
        self.assertIsNotNone(result)
        mock_rms_async.assert_called_once()
        queries = mock_rms_async.call_args[0][0]
        self.assertEqual(queries[0].limit, 5)
        self.assertEqual(queries[0].filter, ['codePostal = "63000"'])
        self.assertEqual(queries[0].sort, ["nom:asc"])

    @patch.object(MeilisearchFFBBClient, "recursive_smart_multi_search_async")
    async def test_search_competitions_async_with_limit(
        self, mock_rms_async: MagicMock
    ) -> None:
        mock_result = MagicMock(spec=CompetitionsMultiSearchResult)
        mock_rms_async.return_value = self._make_mock_results(mock_result)

        result = await self.client.search_competitions_async("U13", limit=7)
        self.assertIsNotNone(result)
        mock_rms_async.assert_called_once()
        queries = mock_rms_async.call_args[0][0]
        self.assertEqual(queries[0].limit, 7)
