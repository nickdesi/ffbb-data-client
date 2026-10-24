"""Tests for the REST endpoints, Best Practices, error envelopes, and caching in api.py."""

from datetime import datetime
from types import SimpleNamespace
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
            mock_client.multi_search.assert_called_with(
                name="Stade Clermontois Basket Auvergne"
            )


@pytest.mark.asyncio
async def test_health_ready_endpoint():
    transport = ASGITransport(app=app)
    mock_client = MagicMock()
    mock_client.get_saisons_async = AsyncMock(return_value=[{"id": "1037"}])
    mock_client.multi_search = MagicMock(return_value=[{"hits": []}])

    with patch("ffbb_data_client.api.get_client", return_value=mock_client):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/health/ready")
            assert r.status_code == 200
            data = r.json()
            assert data.get("status") == "ready"
            assert data.get("checks", {}).get("directus") == "ok"
            assert data.get("checks", {}).get("meilisearch") == "ok"


@pytest.mark.asyncio
async def test_standard_error_envelope_404():
    transport = ASGITransport(app=app)
    mock_client = MagicMock()
    mock_client.get_organisme_async = AsyncMock(return_value=None)

    with patch("ffbb_data_client.api.get_client", return_value=mock_client):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/api/v1/club/999999")
            assert r.status_code == 404
            data = r.json()
            assert "detail" in data
            assert "error" in data
            assert data["error"]["code"] == "NOT_FOUND"
            assert data["error"]["status"] == 404


@pytest.mark.asyncio
async def test_standard_validation_error_422():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid query param length
        r = await ac.get("/api/v1/club/not_a_number")
        assert r.status_code == 422
        data = r.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert len(data["error"]["errors"]) > 0


@pytest.mark.asyncio
async def test_match_card_enrichment_and_pagination():
    transport = ASGITransport(app=app)
    mock_client = MagicMock()
    mock_org = MagicMock()
    mock_org.nom = "STADE CLERMONTOIS BASKET AUVERGNE"
    mock_org.logo = None
    mock_org.engagements = []
    mock_client.get_organisme_async = AsyncMock(return_value=mock_org)

    with patch("ffbb_data_client.api.get_client", return_value=mock_client):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/api/v1/club/9326/matches?limit=10&offset=0")
            assert r.status_code == 200
            assert "Cache-Control" in r.headers
            data = r.json()
            assert "matches" in data
            assert "pagination" in data
            assert data["pagination"]["limit"] == 10
            assert data["pagination"]["offset"] == 0


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
async def test_salle_and_competition_endpoints_caching():
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
            assert "Cache-Control" in r_salle.headers
            assert "max-age=86400" in r_salle.headers["Cache-Control"]

            r_comp = await ac.get("/api/v1/competition/999")
            assert r_comp.status_code == 200
            assert r_comp.json().get("nom") == "DMU13"

            r_saisons = await ac.get("/api/v1/saisons")
            assert r_saisons.status_code == 200
            assert "Cache-Control" in r_saisons.headers
            assert len(r_saisons.json()) == 1


@pytest.mark.asyncio
async def test_club_matches_date_range_filter():
    transport = ASGITransport(app=app)
    mock_client = MagicMock()
    mock_client.get_organisme_async = AsyncMock(
        return_value=SimpleNamespace(
            nom="CLUB TEST",
            logo=None,
            engagements=[
                SimpleNamespace(
                    idPoule=SimpleNamespace(id="111"),
                    idCompetition=SimpleNamespace(nom="DM2", id="5"),
                )
            ],
        )
    )
    # Dates connues par la poule ; 1970 = date absente côté poule
    poule_dates = {
        "1": datetime(2026, 10, 10, 18, 0),
        "2": datetime(2026, 10, 17, 18, 0),
        "3": datetime(2026, 10, 25, 18, 0),
        "4": datetime(1970, 1, 1),
    }
    mock_client.get_poule_async = AsyncMock(
        return_value=SimpleNamespace(
            nom="Poule A",
            rencontres=[
                SimpleNamespace(
                    id=m_id,
                    nomEquipe1="CLUB TEST",
                    nomEquipe2="ADVERSAIRE",
                    idOrganismeEquipe1="42",
                    idOrganismeEquipe2="99",
                    date_rencontre=d,
                )
                for m_id, d in poule_dates.items()
            ],
        )
    )
    detail_dates = {"2": "2026-10-17T18:00:00", "4": "2026-10-14T20:30:00"}
    mock_client.get_rencontre_async = AsyncMock(
        side_effect=lambda m_id: SimpleNamespace(
            id=m_id,
            nomEquipe1="CLUB TEST",
            nomEquipe2="ADVERSAIRE",
            idOrganismeEquipe1=None,
            idOrganismeEquipe2=None,
            date_rencontre=detail_dates.get(m_id, "2026-11-30T18:00:00"),
            salle=None,
        )
    )

    with (
        patch("ffbb_data_client.api.get_client", return_value=mock_client),
        patch(
            "ffbb_data_client.api.resolve_exact_salle_address_async",
            AsyncMock(return_value="Gymnase Test"),
        ),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get(
                "/api/v1/club/42/matches?date_from=2026-10-12&date_to=2026-10-18"
            )
            assert r.status_code == 200
            data = r.json()
            assert [m["ffbbMatchId"] for m in data["matches"]] == ["4", "2"]
            assert data["total"] == 2

    # Les rencontres hors période selon la poule ne sont pas chargées en détail
    fetched = {c.args[0] for c in mock_client.get_rencontre_async.await_args_list}
    assert fetched == {"2", "4"}


@pytest.mark.asyncio
async def test_club_matches_date_range_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get(
            "/api/v1/club/42/matches?date_from=2026-10-18&date_to=2026-10-12"
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "BAD_REQUEST"

        r = await ac.get("/api/v1/club/42/matches?date_from=2026-13-01")
        assert r.status_code == 422
