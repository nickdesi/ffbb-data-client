import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from ffbb_data_client.clients.api_ffbb_app_client import ApiFFBBAppClient
from ffbb_data_client.clients.ffbb_data_client import FFBBDataClient
from ffbb_data_client.clients.meilisearch_client import MeilisearchClient


class TestMeilisearchClientCoverage(unittest.IsolatedAsyncioTestCase):
    def test_bearer_token_property(self):
        client = MeilisearchClient("token123")
        self.assertEqual(client.bearer_token, "token123")

    @patch("ffbb_data_client.clients.meilisearch_client.http_post_json")
    def test_multi_search_success(self, mock_post):
        mock_post.return_value = {"results": [{"hits": []}]}
        client = MeilisearchClient("token123")
        res = client.multi_search([])
        self.assertIsNotNone(res)

    @patch("ffbb_data_client.clients.meilisearch_client.http_post_json")
    def test_multi_search_none_queries(self, mock_post):
        mock_post.return_value = None
        client = MeilisearchClient("token123")
        res = client.multi_search(None)
        self.assertIsNone(res)

    @patch(
        "ffbb_data_client.clients.meilisearch_client.http_post_json_async",
        new_callable=AsyncMock,
    )
    async def test_multi_search_async_http_error(self, mock_post_async):
        mock_post_async.side_effect = httpx.RequestError("error")
        client = MeilisearchClient("token123", debug=True)
        res = await client.multi_search_async([])
        self.assertIsNone(res)

    @patch(
        "ffbb_data_client.clients.meilisearch_client.http_post_json_async",
        new_callable=AsyncMock,
    )
    async def test_multi_search_async_exception(self, mock_post_async):
        mock_post_async.side_effect = Exception("generic error")
        client = MeilisearchClient("token123", debug=True)
        res = await client.multi_search_async([])
        self.assertIsNone(res)


class TestApiFFBBAppClientCoverage(unittest.IsolatedAsyncioTestCase):
    def test_debug_init(self):
        client = ApiFFBBAppClient("token123", debug=True)
        self.assertTrue(client.debug)
        self.assertEqual(client.bearer_token, "token123")

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_configuration(self, mock_get):
        mock_get.return_value = {
            "data": {"id": "1", "key_dh": "a", "key_ms": "b", "maintenance": False}
        }
        client = ApiFFBBAppClient("token123")
        res = client.get_configuration()
        self.assertIsNotNone(res)
        self.assertEqual(res.key_dh, "a")

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_configuration_none(self, mock_get):
        mock_get.return_value = None
        client = ApiFFBBAppClient("token123")
        res = client.get_configuration()
        self.assertIsNone(res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_configuration_async(self, mock_get_async):
        mock_get_async.return_value = {
            "data": {"id": "1", "key_dh": "a", "key_ms": "b", "maintenance": False}
        }
        client = ApiFFBBAppClient("token123")
        res = await client.get_configuration_async()
        self.assertIsNotNone(res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_configuration_async_error(self, mock_get_async):
        mock_get_async.side_effect = Exception("test error")
        client = ApiFFBBAppClient("token123", debug=True)
        res = await client.get_configuration_async()
        self.assertIsNone(res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_lives_async_error(self, mock_get_async):
        mock_get_async.side_effect = Exception("test error")
        client = ApiFFBBAppClient("token123", debug=True)
        res = await client.get_lives_async()
        self.assertIsNone(res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_competition_async_error(self, mock_get_async):
        mock_get_async.side_effect = Exception("test error")
        client = ApiFFBBAppClient("token123", debug=True)
        res = await client.get_competition_async(1)
        self.assertIsNone(res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_poule_async_error(self, mock_get_async):
        mock_get_async.side_effect = Exception("test error")
        client = ApiFFBBAppClient("token123", debug=True)
        res = await client.get_poule_async(1)
        self.assertIsNone(res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_list_competitions_async_error(self, mock_get_async):
        mock_get_async.side_effect = Exception("test error")
        client = ApiFFBBAppClient("token123", debug=True)
        res = await client.list_competitions_async()
        self.assertEqual(res, [])

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_saisons_async_error(self, mock_get_async):
        mock_get_async.side_effect = Exception("test error")
        client = ApiFFBBAppClient("token123", debug=True)
        res = await client.get_saisons_async()
        self.assertEqual(res, [])

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_organisme_async_error(self, mock_get_async):
        mock_get_async.side_effect = Exception("test error")
        client = ApiFFBBAppClient("token123", debug=True)
        res = await client.get_organisme_async(1)
        self.assertIsNone(res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_equipes_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "1", "engagements": []}}
        client = ApiFFBBAppClient("token123")
        res = await client.get_equipes_async(1)
        self.assertIsNotNone(res)

    @patch.object(ApiFFBBAppClient, "get_poule_async", new_callable=AsyncMock)
    async def test_get_classement_async(self, mock_get_poule_async):
        mock_get_poule_async.return_value = MagicMock(classements=["cls"])
        client = ApiFFBBAppClient("token123")
        res = await client.get_classement_async(1)
        self.assertIsNotNone(res)
        self.assertEqual(res, ["cls"])

    def test_list_competitions_none_fields(self):
        client = ApiFFBBAppClient("token")
        with patch(
            "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = {"data": []}
            res = client.list_competitions(fields=None)
            self.assertEqual(res, [])


class TestFFBBDataClientCoverage(unittest.IsolatedAsyncioTestCase):
    def test_create(self):
        client = FFBBDataClient.create(
            "meili_token_with_enough_length", "api_token_with_enough_length"
        )
        self.assertIsNotNone(client)
        self.assertIsNotNone(client.cached_session)
        self.assertIsNotNone(client.async_cached_session)

    def test_create_with_sessions(self):
        session = httpx.Client()
        async_session = httpx.AsyncClient()
        client = FFBBDataClient.create(
            "meili_token_with_enough_length",
            "api_token_with_enough_length",
            cached_session=session,
            async_cached_session=async_session,
        )
        self.assertEqual(client.cached_session, session)
        self.assertEqual(client.async_cached_session, async_session)

    async def test_async_delegations(self):
        api_client = AsyncMock()
        api_client.get_configuration_async.return_value = "config"
        api_client.get_lives_async.return_value = "lives"
        api_client.get_saisons_async.return_value = "saisons"
        api_client.get_competition_async.return_value = "comp"
        api_client.list_competitions_async.return_value = "comps"
        api_client.get_organisme_async.return_value = "org"
        api_client.get_poule_async.return_value = "poule"
        api_client.get_classement_async.return_value = "class"
        api_client.get_equipes_async.return_value = "eq"

        meili_client = AsyncMock()
        meili_client.recursive_smart_multi_search_async.return_value = MagicMock(
            results=["res"]
        )

        client = FFBBDataClient(api_client, meili_client)

        if hasattr(client, "get_configuration_async"):
            self.assertEqual(await client.get_configuration_async(), "config")
        self.assertEqual(await client.get_lives_async(), "lives")
        self.assertEqual(await client.get_saisons_async(), "saisons")
        self.assertEqual(await client.get_competition_async(1), "comp")
        self.assertEqual(await client.list_competitions_async(), "comps")
        self.assertEqual(await client.get_organisme_async(1), "org")
        self.assertEqual(await client.get_poule_async(1), "poule")
        self.assertEqual(await client.get_classement_async(1), "class")
        self.assertEqual(await client.get_equipes_async(1), "eq")

        res_multi = await client.multi_search_async([])
        self.assertIsNotNone(res_multi)

        # async search methods
        self.assertEqual(await client.search_competitions_async("A"), "res")
        self.assertIsNone(await client.search_competitions_async(None))

        self.assertEqual(
            await client.search_multiple_competitions_async(["A"]), ["res"]
        )
        self.assertIsNone(await client.search_multiple_competitions_async(None))

        self.assertEqual(await client.search_organismes_async("A"), "res")
        self.assertIsNone(await client.search_organismes_async(None))
        self.assertEqual(await client.search_multiple_organismes_async(["A"]), ["res"])
        self.assertIsNone(await client.search_multiple_organismes_async(None))

        self.assertEqual(await client.search_pratiques_async("A"), "res")
        self.assertIsNone(await client.search_pratiques_async(None))
        self.assertEqual(await client.search_multiple_pratiques_async(["A"]), ["res"])
        self.assertIsNone(await client.search_multiple_pratiques_async(None))

        # rencontres
        from ffbb_data_client.models.competition_id import CompetitionID
        from ffbb_data_client.models.competition_id_categorie import (
            CompetitionIDCategorie,
        )
        from ffbb_data_client.models.multi_search_result_rencontres import (
            RencontresMultiSearchResult,
        )
        from ffbb_data_client.models.rencontres_hit import RencontresHit

        hit1 = RencontresHit(
            id="1",
            competition_id=CompetitionID(
                id="1", categorie=CompetitionIDCategorie(code="U15", libelle="U15")
            ),
        )
        hit2 = RencontresHit(
            id="2",
            competition_id=CompetitionID(
                id="2", categorie=CompetitionIDCategorie(code="U18", libelle="U18")
            ),
        )

        res_rencontres = RencontresMultiSearchResult(
            hits=[hit1, hit2],
            query="",
            processing_time_ms=0,
            limit=10,
            offset=0,
            estimated_total_hits=2,
        )
        meili_client.recursive_smart_multi_search_async.return_value = MagicMock(
            results=[res_rencontres]
        )

        res = await client.search_rencontres_async("A", categorie="U15")
        self.assertIsNotNone(res)
        self.assertEqual(len(res.hits), 1)

        res = await client.search_multiple_rencontres_async(["A"], categorie="U15")
        self.assertIsNotNone(res)
        self.assertEqual(len(res[0].hits), 1)

        self.assertIsNone(await client.search_rencontres_async(None))
        self.assertIsNone(await client.search_multiple_rencontres_async(None))

        meili_client.recursive_smart_multi_search_async.return_value = MagicMock(
            results=[]
        )
        self.assertIsNone(await client.search_multiple_rencontres_async(["A"]))

        meili_client.recursive_smart_multi_search = MagicMock()
        meili_client.recursive_smart_multi_search.return_value = MagicMock(results=[])
        self.assertIsNone(client.search_multiple_rencontres(["A"]))

        res_rencontres2 = RencontresMultiSearchResult(
            hits=[hit1, hit2],
            query="",
            processing_time_ms=0,
            limit=10,
            offset=0,
            estimated_total_hits=2,
        )
        meili_client.recursive_smart_multi_search.return_value = MagicMock(
            results=[res_rencontres2]
        )
        res_sync = client.search_rencontres("A", categorie="U15")
        self.assertIsNotNone(res_sync)
        self.assertEqual(len(res_sync.hits), 1)

        # salles
        meili_client.recursive_smart_multi_search_async.return_value = MagicMock(
            results=["res"]
        )
        meili_client.recursive_smart_multi_search = MagicMock()
        meili_client.recursive_smart_multi_search.return_value = MagicMock(
            results=["res"]
        )

        self.assertEqual(await client.search_salles_async("A"), "res")
        self.assertIsNone(await client.search_salles_async(None))
        self.assertEqual(await client.search_multiple_salles_async(["A"]), ["res"])
        self.assertIsNone(await client.search_multiple_salles_async(None))

        self.assertEqual(client.search_salles("A"), "res")
        self.assertIsNone(client.search_salles(None))
        self.assertEqual(client.search_multiple_salles(["A"]), ["res"])
        self.assertIsNone(client.search_multiple_salles(None))

        # terrains
        self.assertEqual(client.search_terrains("A"), "res")
        self.assertIsNone(client.search_terrains(None))
        self.assertEqual(client.search_multiple_terrains(["A"]), ["res"])
        self.assertIsNone(client.search_multiple_terrains(None))

        self.assertEqual(await client.search_terrains_async("A"), "res")
        self.assertIsNone(await client.search_terrains_async(None))
        self.assertEqual(await client.search_multiple_terrains_async(["A"]), ["res"])
        self.assertIsNone(await client.search_multiple_terrains_async(None))

        # tournois
        self.assertEqual(client.search_tournois("A"), "res")
        self.assertIsNone(client.search_tournois(None))
        self.assertEqual(client.search_multiple_tournois(["A"]), ["res"])
        self.assertIsNone(client.search_multiple_tournois(None))

        self.assertEqual(await client.search_tournois_async("A"), "res")
        self.assertIsNone(await client.search_tournois_async(None))
        self.assertEqual(await client.search_multiple_tournois_async(["A"]), ["res"])
        self.assertIsNone(await client.search_multiple_tournois_async(None))

        # engagements
        self.assertEqual(client.search_engagements("A"), "res")
        self.assertIsNone(client.search_engagements(None))
        self.assertEqual(client.search_multiple_engagements(["A"]), ["res"])
        self.assertIsNone(client.search_multiple_engagements(None))

        self.assertEqual(await client.search_engagements_async("A"), "res")
        self.assertIsNone(await client.search_engagements_async(None))
        self.assertEqual(await client.search_multiple_engagements_async(["A"]), ["res"])
        self.assertIsNone(await client.search_multiple_engagements_async(None))

        # formations
        self.assertEqual(client.search_formations("A"), "res")
        self.assertIsNone(client.search_formations(None))
        self.assertEqual(client.search_multiple_formations(["A"]), ["res"])
        self.assertIsNone(client.search_multiple_formations(None))

        self.assertEqual(await client.search_formations_async("A"), "res")
        self.assertIsNone(await client.search_formations_async(None))
        self.assertEqual(await client.search_multiple_formations_async(["A"]), ["res"])
        self.assertIsNone(await client.search_multiple_formations_async(None))
