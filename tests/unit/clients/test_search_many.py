from __future__ import annotations

import asyncio
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
        all_started = asyncio.Event()
        started = 0

        def concurrent_result(value):
            async def wait_for_peers(*_args):
                nonlocal started
                started += 1
                if started == 3:
                    all_started.set()
                await asyncio.wait_for(all_started.wait(), timeout=0.5)
                return [value]

            return wait_for_peers

        self.facade.search_multiple_organismes_async.side_effect = concurrent_result(
            "ORG"
        )
        self.facade.search_multiple_competitions_async.side_effect = concurrent_result(
            "COMP"
        )
        self.facade.search_multiple_rencontres_async.side_effect = concurrent_result(
            "REN"
        )

        searches = [
            SearchSpec(resource="organismes", name="a"),
            SearchSpec(resource="competitions", name="b"),
            SearchSpec(resource="rencontres", name="c"),
        ]
        results = await self.facade.search_many_async(searches)

        self.assertEqual(results, [["ORG"], ["COMP"], ["REN"]])
        self.assertEqual(started, 3)

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
