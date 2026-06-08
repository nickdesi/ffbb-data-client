import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from ffbb_data_client.clients.api_ffbb_app_client import ApiFFBBAppClient
from ffbb_data_client.clients.ffbb_data_client import FFBBDataClient


class TestNewMethodsCoverage(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bearer_token = "test_token"
        self.api_client = ApiFFBBAppClient(self.bearer_token)
        # MeilisearchFFBBClient requires a MeilisearchClient
        self.ms_core_client = MagicMock()
        self.ms_client = MagicMock()  # MeilisearchFFBBClient
        self.main_client = FFBBDataClient(self.api_client, self.ms_client)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_rencontre(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_rencontre("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_rencontre", return_value=res):
            res_v3 = self.main_client.get_rencontre("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_rencontre_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_rencontre_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_rencontre_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_rencontre_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_engagement(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_engagement("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_engagement", return_value=res):
            res_v3 = self.main_client.get_engagement("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_engagement_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_engagement_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_engagement_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_engagement_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_formation(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_formation("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_formation", return_value=res):
            res_v3 = self.main_client.get_formation("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_formation_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_formation_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_formation_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_formation_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_entraineur(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_entraineur("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_entraineur", return_value=res):
            res_v3 = self.main_client.get_entraineur("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_entraineur_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_entraineur_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_entraineur_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_entraineur_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_commune(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_commune("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_commune", return_value=res):
            res_v3 = self.main_client.get_commune("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_commune_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_commune_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_commune_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_commune_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_officiel(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_officiel("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_officiel", return_value=res):
            res_v3 = self.main_client.get_officiel("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_officiel_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_officiel_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_officiel_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_officiel_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_salle(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_salle("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_salle", return_value=res):
            res_v3 = self.main_client.get_salle("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_salle_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_salle_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_salle_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_salle_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_terrain(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_terrain("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_terrain", return_value=res):
            res_v3 = self.main_client.get_terrain("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_terrain_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_terrain_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_terrain_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_terrain_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_tournoi(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_tournoi("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_tournoi", return_value=res):
            res_v3 = self.main_client.get_tournoi("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_tournoi_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_tournoi_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_tournoi_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_tournoi_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    def test_get_pratique(self, mock_get):
        mock_get.return_value = {"data": {"id": "123"}}
        res = self.api_client.get_pratique("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(self.api_client, "get_pratique", return_value=res):
            res_v3 = self.main_client.get_pratique("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_pratique_async(self, mock_get_async):
        mock_get_async.return_value = {"data": {"id": "123"}}
        res = await self.api_client.get_pratique_async("123")
        self.assertIsNotNone(res)
        self.assertEqual(res.id, "123")

        # Test delegation
        with patch.object(
            self.api_client, "get_pratique_async", new_callable=AsyncMock
        ) as mock_delegate:
            mock_delegate.return_value = res
            res_v3 = await self.main_client.get_pratique_async("123")
            self.assertEqual(res_v3, res)

    @patch(
        "ffbb_data_client.clients.api_ffbb_app_client.http_get_json_async",
        new_callable=AsyncMock,
    )
    async def test_get_rencontre_async_error(self, mock_get_async):
        mock_get_async.side_effect = Exception("API error")
        res = await self.api_client.get_rencontre_async("123")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
