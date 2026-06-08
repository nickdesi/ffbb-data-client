from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ReadTimeout

from ffbb_data_client.clients.api_ffbb_app_client import ApiFFBBAppClient
from ffbb_data_client.clients.ffbb_data_client import FFBBDataClient
from ffbb_data_client.helpers.http_requests_helper import async_catch_result
from ffbb_data_client.helpers.meilisearch_client_extension import (
    MeilisearchClientExtension,
)
from ffbb_data_client.models.multi_search_query import MultiSearchQuery
from ffbb_data_client.models.multi_search_results import MultiSearchResult
from ffbb_data_client.models.multi_search_results_class import MultiSearchResults


class _Hit:
    def __init__(self, valid: bool = True) -> None:
        self.valid = valid

    def is_valid_for_query(self, lower_q: str) -> bool:
        return self.valid and lower_q == "senas"


class _Tokens:
    meilisearch_token = "meili-token-valid"
    api_token = "api-token-valid"


class TestTargetedHttpAsyncHelperCoverage(unittest.IsolatedAsyncioTestCase):
    async def test_async_catch_result_success(self) -> None:
        async def ok() -> str:
            return "ok"

        self.assertEqual(await async_catch_result(ok()), "ok")

    async def test_async_catch_result_empty_json_returns_none(self) -> None:
        async def broken() -> None:
            raise json.decoder.JSONDecodeError("Expecting value", "", 0)

        self.assertIsNone(await async_catch_result(broken()))

    async def test_async_catch_result_other_json_error_raises(self) -> None:
        async def broken() -> None:
            raise json.decoder.JSONDecodeError("Other", "", 0)

        with self.assertRaises(json.decoder.JSONDecodeError):
            await async_catch_result(broken())

    async def test_async_catch_result_timeout_first_attempt_returns_none(self) -> None:
        async def broken() -> None:
            raise ReadTimeout("timeout")

        self.assertIsNone(await async_catch_result(broken()))

    async def test_async_catch_result_timeout_retry_attempt_raises(self) -> None:
        async def broken() -> None:
            raise ReadTimeout("timeout")

        with self.assertRaises(ReadTimeout):
            await async_catch_result(broken(), is_retrieving=True)

    async def test_async_catch_result_connection_retry_attempt_raises(self) -> None:
        async def broken() -> None:
            raise ConnectionError("down")

        with self.assertRaises(ConnectionError):
            await async_catch_result(broken(), is_retrieving=True)


class TestTargetedMeilisearchExtensionCoverage(unittest.IsolatedAsyncioTestCase):
    def _client(self) -> MeilisearchClientExtension:
        return MeilisearchClientExtension("token", "https://example.test/")

    def test_smart_multi_search_filters_only_queries_with_q(self) -> None:
        client = self._client()
        result_with_q = MultiSearchResult(
            hits=[_Hit(True), _Hit(False)], estimated_total_hits=2
        )
        result_without_q = MultiSearchResult(hits=[_Hit(False)], estimated_total_hits=1)
        queries = [MultiSearchQuery(q="Senas"), MultiSearchQuery(q=None)]
        client.multi_search = MagicMock(
            return_value=MultiSearchResults([result_with_q, result_without_q])
        )

        result = client.smart_multi_search(queries)

        self.assertIsNotNone(result)
        assert result is not None and result.results is not None
        self.assertEqual(len(result.results[0].hits or []), 1)
        self.assertEqual(len(result.results[1].hits or []), 1)

    async def test_smart_multi_search_async_filters_results(self) -> None:
        client = self._client()
        result_with_q = MultiSearchResult(
            hits=[_Hit(True), _Hit(False)], estimated_total_hits=2
        )
        client.multi_search_async = AsyncMock(
            return_value=MultiSearchResults([result_with_q])
        )

        result = await client.smart_multi_search_async([MultiSearchQuery(q="Senas")])

        self.assertIsNotNone(result)
        assert result is not None and result.results is not None
        self.assertEqual(len(result.results[0].hits or []), 1)

    def test_recursive_search_extends_hits_and_alias_delegates(self) -> None:
        client = self._client()
        first = MultiSearchResults(
            [
                MultiSearchResult(
                    hits=[_Hit()], estimated_total_hits=3, offset=0, limit=1
                )
            ]
        )
        second = MultiSearchResults(
            [
                MultiSearchResult(
                    hits=[_Hit(), _Hit()], estimated_total_hits=3, offset=1, limit=2
                )
            ]
        )
        client.smart_multi_search = MagicMock(side_effect=[first, second])
        query = MultiSearchQuery(q=None, limit=1, offset=0)

        result = client.recursive_multi_search([query])

        self.assertIs(result, first)
        self.assertEqual(len(first.results[0].hits), 3)  # type: ignore[index,union-attr,arg-type]
        self.assertEqual(query.offset, 1)
        self.assertEqual(query.limit, 2)

    async def test_recursive_search_async_extends_hits(self) -> None:
        client = self._client()
        first = MultiSearchResults(
            [
                MultiSearchResult(
                    hits=[_Hit()], estimated_total_hits=2, offset=0, limit=1
                )
            ]
        )
        second = MultiSearchResults(
            [
                MultiSearchResult(
                    hits=[_Hit()], estimated_total_hits=2, offset=1, limit=1
                )
            ]
        )
        client.smart_multi_search_async = AsyncMock(side_effect=[first, second])

        result = await client.recursive_smart_multi_search_async(
            [MultiSearchQuery(limit=1, offset=0)]
        )

        self.assertIs(result, first)
        self.assertEqual(len(first.results[0].hits), 2)  # type: ignore[index,union-attr,arg-type]

    def test_recursive_search_returns_early_for_empty_results(self) -> None:
        client = self._client()
        client.smart_multi_search = MagicMock(
            return_value=MultiSearchResults(results=[])
        )

        result = client.recursive_smart_multi_search([MultiSearchQuery()])

        self.assertEqual(result, MultiSearchResults(results=[]))


class TestTargetedApiFFBBAppClientCoverage(unittest.IsolatedAsyncioTestCase):
    def _client(self) -> ApiFFBBAppClient:
        return ApiFFBBAppClient("api-token", url="https://api.example/")

    def test_constructor_rejects_blank_token_and_exposes_bearer_token(self) -> None:
        with self.assertRaises(ValueError):
            ApiFFBBAppClient("   ")

        client = self._client()
        self.assertEqual(client.bearer_token, "api-token")
        self.assertEqual(client.headers["Authorization"], "Bearer api-token")

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_directus_item_extracts_nested_data_and_fields(
        self, mock_get: MagicMock
    ) -> None:
        mock_get.return_value = {"data": {"id": "1", "nom": "Club"}}
        client = self._client()

        result = client._get_directus_item("items", 1, fields=["id", "nom"])

        self.assertEqual(result, {"id": "1", "nom": "Club"})
        called_url = mock_get.call_args.args[0]
        self.assertIn("https://api.example/items/1", called_url)
        self.assertIn("fields%5B%5D=id", called_url)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_directus_item_handles_raw_dict_and_non_dict(
        self, mock_get: MagicMock
    ) -> None:
        client = self._client()
        mock_get.return_value = {"id": "raw"}
        self.assertIsNone(client._get_directus_item("items", 1))

        mock_get.return_value = {"data": ["not", "dict"]}
        self.assertIsNone(client._get_directus_item("items", 1))

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_list_directus_items_extracts_lists_and_defaults_empty(
        self, mock_get: MagicMock
    ) -> None:
        client = self._client()
        mock_get.return_value = {"data": [{"id": 1}]}
        result = client._list_directus_items(
            "items",
            limit=5,
            fields=["id"],
            filter_criteria='{"id":{"_eq":1}}',
            sort=["id"],
            offset=10,
            search="abc",
        )
        self.assertEqual(result, [{"id": 1}])
        called_url = mock_get.call_args.args[0]
        self.assertIn("limit=5", called_url)
        self.assertIn("offset=10", called_url)
        self.assertIn("search=abc", called_url)

        mock_get.return_value = {"data": {"not": "list"}}
        self.assertEqual(client._list_directus_items("items"), [])

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_async_directus_helpers_success_and_failure(
        self, mock_get: AsyncMock
    ) -> None:
        client = self._client()
        mock_get.return_value = {"data": {"id": "1"}}
        self.assertEqual(await client._get_directus_item_async("items", 1), {"id": "1"})

        mock_get.return_value = {"data": [{"id": "1"}]}
        self.assertEqual(
            await client._list_directus_items_async("items"), [{"id": "1"}]
        )

        mock_get.side_effect = RuntimeError("boom")
        self.assertIsNone(await client._get_directus_item_async("items", 1))
        self.assertEqual(await client._list_directus_items_async("items"), [])

    async def test_typed_list_wrappers_convert_raw_items_sync_and_async(self) -> None:
        client = self._client()
        raw = [{"id": 1}, None]
        client._list_directus_items = MagicMock(return_value=raw)  # type: ignore[method-assign]
        client._list_directus_items_async = AsyncMock(return_value=raw)  # type: ignore[method-assign]

        sync_names = [
            "list_rencontres",
            "list_salles",
            "list_terrains",
            "list_tournois",
            "list_engagements",
            "list_formations",
            "list_entraineurs",
            "list_communes",
            "list_officiels",
            "list_pratiques",
        ]
        for name in sync_names:
            result = getattr(client, name)(limit=1, offset=2, search="abc")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].id, "1")

        for name in [f"{name}_async" for name in sync_names]:
            result = await getattr(client, name)(limit=1, offset=2, search="abc")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].id, "1")


class TestTargetedFFBBDataClientCoverage(unittest.IsolatedAsyncioTestCase):
    def test_chunked_handles_empty_and_partial_chunks(self) -> None:
        from ffbb_data_client.clients._rest_facade import _RestFacade

        self.assertEqual(_RestFacade._chunked([], 2), [])
        self.assertEqual(
            _RestFacade._chunked([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]]
        )

    @patch("ffbb_data_client.clients.ffbb_data_client.MeilisearchFFBBClient")
    @patch("ffbb_data_client.clients.ffbb_data_client.ApiFFBBAppClient")
    @patch("ffbb_data_client.clients.ffbb_data_client.CacheManager")
    @patch(
        "ffbb_data_client.clients.ffbb_data_client.TokenManager.get_tokens",
        return_value=_Tokens(),
    )
    def test_create_resolves_tokens_validates_and_wires_clients(
        self,
        mock_tokens: MagicMock,
        mock_cache_manager: MagicMock,
        mock_api_cls: MagicMock,
        mock_meili_cls: MagicMock,
    ) -> None:
        cache = MagicMock()
        cache.session = "sync-session"
        cache.async_session = "async-session"
        mock_cache_manager.return_value = cache
        mock_api = MagicMock()
        mock_api.cached_session = "sync-session"
        mock_api.async_cached_session = "async-session"
        mock_api_cls.return_value = mock_api
        mock_meili = MagicMock()
        mock_meili_cls.return_value = mock_meili

        client = FFBBDataClient.create(debug=True)

        self.assertIs(client.api_ffbb_client, mock_api)
        self.assertIs(client.meilisearch_ffbb_client, mock_meili)
        mock_tokens.assert_called_once()
        mock_api_cls.assert_called_once_with(
            "api-token-valid",
            debug=True,
            cached_session="sync-session",
            async_cached_session="async-session",
        )
        mock_meili_cls.assert_called_once_with(
            "meili-token-valid",
            debug=True,
            cached_session="sync-session",
            async_cached_session="async-session",
        )

    async def test_facade_delegates_sync_and_async_methods(self) -> None:
        api = MagicMock()
        api.cached_session = "sync"
        api.async_cached_session = "async"
        api.get_organisme_for_search.return_value = "club"
        api.get_organisme_for_search_async = AsyncMock(return_value="club-async")
        api.get_configuration.return_value = "config"
        api.get_configuration_async = AsyncMock(return_value="config-async")
        api.get_competition.return_value = "competition"
        api.list_competitions.return_value = ["competition"]
        meili = MagicMock()
        client = FFBBDataClient(api, meili)

        self.assertEqual(client.cached_session, "sync")
        self.assertEqual(client.async_cached_session, "async")
        self.assertEqual(client.get_organisme_for_search(1), "club")
        self.assertEqual(await client.get_organisme_for_search_async(1), "club-async")
        self.assertEqual(client.get_configuration(), "config")
        self.assertEqual(await client.get_configuration_async(), "config-async")
        self.assertEqual(client.get_competition(2), "competition")
        self.assertEqual(client.list_competitions(limit=1), ["competition"])

    def test_directus_extra_sync_delegations_forward_arguments(self) -> None:
        api = MagicMock()
        meili = MagicMock()
        client = FFBBDataClient(api, meili)
        fields = ["id"]
        filter_criteria = '{"active":{"_eq":true}}'
        sort = ["id"]

        simple_calls = [
            ("get_openapi_spec", (), "get_openapi_spec", ()),
            ("get_session", ("s1",), "get_session", ("s1",)),
            ("get_genius_sport_match", ("g1",), "get_genius_sport_match", ("g1",)),
            ("get_rematch_video", ("r1",), "get_rematch_video", ("r1",)),
            ("get_edf_match", (1,), "get_edf_match", (1,)),
            ("get_edf_player", (2,), "get_edf_player", (2,)),
        ]
        for facade_name, args, api_name, api_args in simple_calls:
            getattr(api, api_name).return_value = facade_name
            self.assertEqual(
                (
                    getattr(client, facade_name)(*args, fields=fields)
                    if args
                    else getattr(client, facade_name)(*args)
                ),
                facade_name,
            )
            if api_args:
                getattr(api, api_name).assert_called_with(*api_args, fields=fields)
            else:
                getattr(api, api_name).assert_called_with()

        list_calls = [
            "list_sessions",
            "list_genius_sport_matches",
            "list_genius_sports_live_logs",
            "list_rematch_videos",
            "list_edf_matches",
            "list_edf_players",
            "list_edf_teams",
            "list_edf_rosters",
        ]
        for name in list_calls:
            getattr(api, name).return_value = [name]
            self.assertEqual(
                getattr(client, name)(
                    limit=3, fields=fields, filter_criteria=filter_criteria, sort=sort
                ),
                [name],
            )
            getattr(api, name).assert_called_with(
                limit=3, fields=fields, filter_criteria=filter_criteria, sort=sort
            )

    async def test_directus_extra_async_delegations_forward_arguments(self) -> None:
        api = MagicMock()
        meili = MagicMock()
        client = FFBBDataClient(api, meili)
        fields = ["id"]
        filter_criteria = '{"active":{"_eq":true}}'
        sort = ["id"]

        for name in [
            "get_session_async",
            "get_genius_sport_match_async",
            "get_rematch_video_async",
        ]:
            setattr(api, name, AsyncMock(return_value=name))
            self.assertEqual(await getattr(client, name)("item", fields=fields), name)
            getattr(api, name).assert_awaited_with("item", fields=fields)

        for name in [
            "list_sessions_async",
            "list_genius_sport_matches_async",
            "list_rematch_videos_async",
        ]:
            setattr(api, name, AsyncMock(return_value=[name]))
            self.assertEqual(
                await getattr(client, name)(
                    limit=4, fields=fields, filter_criteria=filter_criteria, sort=sort
                ),
                [name],
            )
            getattr(api, name).assert_awaited_with(
                limit=4, fields=fields, filter_criteria=filter_criteria, sort=sort
            )

    def test_batch_helpers_build_filters_and_merge_chunks(self) -> None:
        api = MagicMock()
        meili = MagicMock()
        client = FFBBDataClient(api, meili)
        client._rest._BATCH_CHUNK_SIZE = 2
        client._rest.list_engagements = MagicMock(side_effect=[["e1"], ["e2"]])
        client._rest.list_rencontres = MagicMock(side_effect=[["r1"], ["r2"]])
        client._rest.list_entraineurs = MagicMock(side_effect=[["c1"], ["c2"]])

        self.assertEqual(client.list_engagements_by_ids([1, 2, 3]), ["e1", "e2"])
        self.assertEqual(client.list_rencontres_by_poules([7, 8, 9]), ["r1", "r2"])
        self.assertEqual(client.list_entraineurs_by_ids([11, 12, 13]), ["c1", "c2"])

        self.assertIn(
            '"id": {"_in": [1, 2]}',
            client._rest.list_engagements.call_args_list[0].kwargs["filter_criteria"],
        )
        self.assertIn(
            '"idPoule": {"_in": [7, 8]}',
            client._rest.list_rencontres.call_args_list[0].kwargs["filter_criteria"],
        )
        self.assertIn(
            '"idLicence": {"_in": ["11", "12"]}',
            client._rest.list_entraineurs.call_args_list[0].kwargs["filter_criteria"],
        )

    async def test_list_all_and_typed_list_delegations_forward_validated_arguments(
        self,
    ) -> None:
        api = MagicMock()
        meili = MagicMock()
        client = FFBBDataClient(api, meili)
        filter_criteria = '{"id":{"_eq":1}}'
        sort = ["id"]

        for name in [
            "list_rencontres",
            "list_salles",
            "list_terrains",
            "list_tournois",
            "list_engagements",
            "list_formations",
            "list_entraineurs",
            "list_communes",
            "list_officiels",
            "list_pratiques",
        ]:
            getattr(api, name).return_value = [name]
            self.assertEqual(
                getattr(client, name)(
                    limit=2,
                    filter_criteria=filter_criteria,
                    sort=sort,
                    offset=1,
                    search="abc",
                ),
                [name],
            )
            getattr(api, name).assert_called_with(
                limit=2,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=1,
                search="abc",
                cached_session=None,
            )

        for name in [
            "list_all_rencontres",
            "list_all_salles",
            "list_all_terrains",
            "list_all_tournois",
            "list_all_engagements",
            "list_all_formations",
            "list_all_entraineurs",
            "list_all_communes",
            "list_all_officiels",
            "list_all_pratiques",
        ]:
            getattr(api, name).return_value = [name]
            self.assertEqual(
                getattr(client, name)(
                    filter_criteria=filter_criteria,
                    sort=sort,
                    search="abc",
                    page_size=5,
                    max_items=6,
                ),
                [name],
            )
            getattr(api, name).assert_called_with(
                filter_criteria=filter_criteria,
                sort=sort,
                search="abc",
                page_size=5,
                max_items=6,
                cached_session=None,
            )

        for name in [
            "list_rencontres_async",
            "list_salles_async",
            "list_terrains_async",
            "list_tournois_async",
            "list_engagements_async",
            "list_formations_async",
            "list_entraineurs_async",
            "list_communes_async",
            "list_officiels_async",
            "list_pratiques_async",
        ]:
            setattr(api, name, AsyncMock(return_value=[name]))
            self.assertEqual(
                await getattr(client, name)(
                    limit=2,
                    filter_criteria=filter_criteria,
                    sort=sort,
                    offset=1,
                    search="abc",
                ),
                [name],
            )
            getattr(api, name).assert_awaited_with(
                limit=2,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=1,
                search="abc",
                cached_session=None,
            )

        for name in [
            "list_all_rencontres_async",
            "list_all_salles_async",
            "list_all_terrains_async",
            "list_all_tournois_async",
            "list_all_engagements_async",
            "list_all_formations_async",
            "list_all_entraineurs_async",
            "list_all_communes_async",
            "list_all_officiels_async",
            "list_all_pratiques_async",
        ]:
            setattr(api, name, AsyncMock(return_value=[name]))
            self.assertEqual(
                await getattr(client, name)(
                    filter_criteria=filter_criteria,
                    sort=sort,
                    search="abc",
                    page_size=5,
                    max_items=6,
                ),
                [name],
            )
            getattr(api, name).assert_awaited_with(
                filter_criteria=filter_criteria,
                sort=sort,
                search="abc",
                page_size=5,
                max_items=6,
                cached_session=None,
            )

    def test_search_wrappers_cover_empty_single_multiple_and_geo_delegations(
        self,
    ) -> None:
        api = MagicMock()
        meili = MagicMock()
        client = FFBBDataClient(api, meili)
        result = MultiSearchResult(hits=[], estimated_total_hits=0)
        meili.recursive_smart_multi_search.return_value = MultiSearchResults([result])

        families = [
            "competitions",
            "organismes",
            "pratiques",
            "salles",
            "terrains",
            "tournois",
            "engagements",
            "formations",
            "news",
            "youtube_videos",
            "rss",
            "galeries",
        ]
        for family in families:
            self.assertIsNone(getattr(client, f"search_multiple_{family}")([]))
            self.assertEqual(
                getattr(client, f"search_multiple_{family}")(
                    ["abc"], filter=["f"], sort=["s"], limit=7
                ),
                [result],
            )
            self.assertIs(
                getattr(client, f"search_{family}")(
                    "abc", filter=["f"], sort=["s"], limit=7
                ),
                result,
            )
            self.assertIsNone(getattr(client, f"search_{family}")(None))

        meili.search_organismes_by_geo.return_value = "organismes-geo"
        meili.search_organismes_by_city.return_value = "organismes-city"
        meili.search_salles_by_geo.return_value = "salles-geo"
        meili.search_engagements_by_geo.return_value = "engagements-geo"
        meili.search_engagements_filtered.return_value = "engagements-filtered"

        self.assertEqual(client.search_organismes_by_geo(1.0, 2.0), "organismes-geo")
        self.assertEqual(client.search_organismes_by_city("Paris"), "organismes-city")
        self.assertEqual(client.search_salles_by_geo(1.0, 2.0), "salles-geo")
        self.assertEqual(client.search_engagements_by_geo(1.0, 2.0), "engagements-geo")
        self.assertEqual(
            client.search_engagements_filtered(
                1.0, 2.0, sexes=["M"], niveau_codes=["R1"]
            ),
            "engagements-filtered",
        )

    async def test_search_wrappers_cover_async_empty_and_results(self) -> None:
        api = MagicMock()
        meili = MagicMock()
        client = FFBBDataClient(api, meili)
        result = MultiSearchResult(hits=[], estimated_total_hits=0)
        meili.recursive_smart_multi_search_async = AsyncMock(
            return_value=MultiSearchResults([result])
        )

        families = [
            "competitions",
            "organismes",
            "pratiques",
            "salles",
            "terrains",
            "tournois",
            "engagements",
            "formations",
        ]
        for family in families:
            self.assertIsNone(
                await getattr(client, f"search_multiple_{family}_async")([])
            )
            self.assertEqual(
                await getattr(client, f"search_multiple_{family}_async")(
                    ["abc"], filter=["f"], sort=["s"], limit=7
                ),
                [result],
            )
            self.assertIs(
                await getattr(client, f"search_{family}_async")("abc"), result
            )
            self.assertIsNone(await getattr(client, f"search_{family}_async")(None))

    async def test_search_rencontres_filters_by_category_sync_and_async(self) -> None:
        api = MagicMock()
        meili = MagicMock()
        client = FFBBDataClient(api, meili)
        kept = SimpleNamespace(
            competition_id=SimpleNamespace(
                categorie=SimpleNamespace(code="U11M", libelle="U11 Masculin")
            )
        )
        dropped = SimpleNamespace(
            competition_id=SimpleNamespace(
                categorie=SimpleNamespace(code="U13M", libelle="U13 Masculin")
            )
        )
        missing = SimpleNamespace(competition_id=None)
        sync_result = MultiSearchResult(
            hits=[kept, dropped, missing], estimated_total_hits=3
        )
        async_result = MultiSearchResult(hits=[kept, dropped], estimated_total_hits=2)
        meili.recursive_smart_multi_search.return_value = MultiSearchResults(
            [sync_result]
        )
        meili.recursive_smart_multi_search_async = AsyncMock(
            return_value=MultiSearchResults([async_result])
        )

        self.assertIsNone(client.search_multiple_rencontres([]))
        filtered = client.search_multiple_rencontres(["club"], categorie="U11M")
        self.assertIsNotNone(filtered)
        assert filtered is not None
        self.assertEqual(filtered[0].hits, [kept])
        self.assertEqual(filtered[0].estimated_total_hits, 1)
        self.assertIs(client.search_rencontres("club", categorie="U11M"), filtered[0])
        self.assertIsNone(client.search_rencontres(None))

        self.assertIsNone(await client.search_multiple_rencontres_async([]))
        filtered_async = await client.search_multiple_rencontres_async(
            ["club"], categorie="U11M"
        )
        self.assertIsNotNone(filtered_async)
        assert filtered_async is not None
        self.assertEqual(filtered_async[0].hits, [kept])
        self.assertEqual(filtered_async[0].estimated_total_hits, 1)
        self.assertIs(
            await client.search_rencontres_async("club", categorie="U11M"),
            filtered_async[0],
        )
        self.assertIsNone(await client.search_rencontres_async(None))


if __name__ == "__main__":
    unittest.main()
