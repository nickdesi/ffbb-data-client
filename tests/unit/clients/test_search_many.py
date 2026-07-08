from __future__ import annotations

import asyncio
import time
import unittest
from unittest.mock import AsyncMock, MagicMock

from ffbb_data_client import SearchSpec
from ffbb_data_client.clients._search_facade import _SearchFacade


class TestSearchMany(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.facade = _SearchFacade(MagicMock(), MagicMock())
        self.organismes_mock = AsyncMock(return_value=["ORG"])
        self.competitions_mock = AsyncMock(return_value=["COMP"])
        self.rencontres_mock = AsyncMock(return_value=["REN"])
        self.facade.search_multiple_organismes_async = self.organismes_mock
        self.facade.search_multiple_competitions_async = self.competitions_mock
        self.facade.search_multiple_rencontres_async = self.rencontres_mock

    async def test_search_many_async_preserves_order(self):
        searches = [
            SearchSpec(resource="organismes", name="Paris"),
            SearchSpec(resource="competitions", names=["Pro A", "Pro B"]),
            SearchSpec(resource="rencontres", name="J1", categorie="U13"),
        ]
        results = await self.facade.search_many_async(searches)

        self.assertEqual(results, [["ORG"], ["COMP"], ["REN"]])
        self.organismes_mock.assert_called_once_with(["Paris"], None, None, 10)
        self.competitions_mock.assert_called_once_with(
            ["Pro A", "Pro B"], None, None, 10
        )
        self.rencontres_mock.assert_called_once_with(["J1"], "U13")

    async def test_search_many_async_runs_concurrently(self):
        sleep = 0.02

        async def _slow_organismes(names, filter, sort, limit):
            await asyncio.sleep(sleep)
            return ["ORG"]

        async def _slow_competitions(names, filter, sort, limit):
            await asyncio.sleep(sleep)
            return ["COMP"]

        async def _slow_rencontres(names, categorie):
            await asyncio.sleep(sleep)
            return ["REN"]

        self.facade.search_multiple_organismes_async.side_effect = _slow_organismes
        self.facade.search_multiple_competitions_async.side_effect = _slow_competitions
        self.facade.search_multiple_rencontres_async.side_effect = _slow_rencontres

        searches = [
            SearchSpec(resource="organismes", name="a"),
            SearchSpec(resource="competitions", name="b"),
            SearchSpec(resource="rencontres", name="c"),
        ]
        start = time.monotonic()
        results = await self.facade.search_many_async(searches)
        elapsed = time.monotonic() - start

        self.assertEqual(results, [["ORG"], ["COMP"], ["REN"]])
        self.assertLess(elapsed, sleep * 2)

    async def test_search_many_empty_returns_empty(self):
        self.assertEqual(await self.facade.search_many_async([]), [])

    async def test_search_many_unknown_resource_raises(self):
        with self.assertRaises(ValueError):
            await self.facade.search_many_async([SearchSpec(resource="inconnu")])

    async def test_search_many_sync_variant(self):
        searches = [
            SearchSpec(resource="organismes", name="Paris"),
            SearchSpec(resource="competitions", name="Pro A"),
            SearchSpec(resource="rencontres", name="J1", categorie="U13"),
        ]
        sync_results = self.facade.search_many(searches)
        async_results = await self.facade.search_many_async(searches)
        self.assertEqual(sync_results, async_results)
        self.assertEqual(sync_results, [["ORG"], ["COMP"], ["REN"]])

    async def test_search_many_name_only(self):
        await self.facade.search_many_async(
            [SearchSpec(resource="organismes", name="Paris")]
        )
        self.organismes_mock.assert_called_once_with(["Paris"], None, None, 10)


if __name__ == "__main__":
    unittest.main()
