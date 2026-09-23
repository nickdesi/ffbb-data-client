"""Tests for the new REST endpoints and match card enrichment in api.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from ffbb_data_client.api import app


@pytest.mark.asyncio
async def test_search_acronym_expansion():
    transport = ASGITransport(app=app)
    mock_client = MagicMock()
    mock_client.multi_search = MagicMock(
        return_value=[
            {"index_uid": "organismes", "hits": [{"nom": "STADE CLERMONTOIS"}]}
        ]
    )
    with patch("ffbb_data_client.api.get_client", return_value=mock_client):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/api/v1/search?query=SCBA")
            assert r.status_code == 200
            # Ensure multi_search was called with expanded name
            mock_client.multi_search.assert_called_with(
                name="Stade Clermontois Basket Auvergne"
            )


@pytest.mark.asyncio
async def test_match_card_enrichment():
    transport = ASGITransport(app=app)
    mock_client = MagicMock()
    mock_org = MagicMock()
    mock_org.nom = "STADE CLERMONTOIS BASKET AUVERGNE"
    mock_org.logo = None
    mock_org.engagements = []
    mock_client.get_organisme_async = AsyncMock(return_value=mock_org)

    with patch("ffbb_data_client.api.get_client", return_value=mock_client):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/api/v1/club/9326/matches")
            assert r.status_code == 200
            data = r.json()
            assert "matches" in data


@pytest.mark.asyncio
async def test_rencontre_endpoint():
    transport = ASGITransport(app=app)
    mock_client = MagicMock()
    mock_match = {"id": "12345", "nomEquipe1": "Eq A", "nomEquipe2": "Eq B"}
    mock_client.get_rencontre_async = AsyncMock(return_value=mock_match)

    with patch("ffbb_data_client.api.get_client", return_value=mock_client):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/api/v1/rencontre/12345")
            assert r.status_code == 200
            assert r.json().get("id") == "12345"

            # Test alias /match
            r_alias = await ac.get("/api/v1/match/12345")
            assert r_alias.status_code == 200


@pytest.mark.asyncio
async def test_salle_and_competition_endpoints():
    transport = ASGITransport(app=app)
    mock_client = MagicMock()
    mock_client.get_salle_async = AsyncMock(
        return_value={"id": "6543", "libelle": "Gymnase Fleury"}
    )
    mock_client.get_competition_async = AsyncMock(
        return_value={"id": "999", "nom": "DMU13"}
    )
    mock_client.get_saisons_async = AsyncMock(
        return_value=[{"id": "1037", "nom": "2026-2027"}]
    )

    with patch("ffbb_data_client.api.get_client", return_value=mock_client):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r_salle = await ac.get("/api/v1/salle/6543")
            assert r_salle.status_code == 200
            assert r_salle.json().get("libelle") == "Gymnase Fleury"

            r_comp = await ac.get("/api/v1/competition/999")
            assert r_comp.status_code == 200
            assert r_comp.json().get("nom") == "DMU13"

            r_saisons = await ac.get("/api/v1/saisons")
            assert r_saisons.status_code == 200
            assert len(r_saisons.json()) == 1
