"""Tests for new API features: classement, equipes, categorie filtering, retry."""

import pytest
import respx

from ffbb_data_client.clients.api_ffbb_app_client import ApiFFBBAppClient
from ffbb_data_client.clients.ffbb_data_client import FFBBDataClient
from ffbb_data_client.clients.meilisearch_ffbb_client import MeilisearchFFBBClient
from ffbb_data_client.exceptions import FFBBServerError


# ---------------------------------------------------------------------------
# Feature 1: get_classement_async
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_classement_async():
    """get_classement_async should return a poule with classements only."""
    client = ApiFFBBAppClient(bearer_token="test-token")
    poule_id = 123

    with respx.mock:
        respx.get(
            url__startswith=f"https://api.ffbb.app/items/ffbbserver_poules/{poule_id}"
        ).respond(
            json={
                "data": {
                    "id": str(poule_id),
                    "classements": [
                        {
                            "id": "c1",
                            "position": 1,
                            "points": 10,
                            "matchJoues": 5,
                            "gagnes": 4,
                            "perdus": 1,
                            "nombreForfaits": 0,
                            "paniersMarques": 100,
                            "paniersEncaisses": 80,
                            "difference": 20,
                            "quotient": 1.25,
                        }
                    ],
                }
            }
        )

        result = await client.get_classement_async(poule_id)
        assert result is not None
        assert len(result) == 1
        assert result[0].position == 1
        assert result[0].points == 10


# ---------------------------------------------------------------------------
# Feature 2: get_equipes_async
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_equipes_async():
    """get_equipes_async should return an organisme with engagements only."""
    client = ApiFFBBAppClient(bearer_token="test-token")
    organisme_id = 456

    with respx.mock:
        respx.get(
            url__startswith=f"https://api.ffbb.app/items/ffbbserver_organismes/{organisme_id}"
        ).respond(
            json={
                "data": {
                    "id": str(organisme_id),
                    "nom": "Club Test",
                    "code": "123",
                    "telephone": "",
                    "adresse": "",
                    "mail": "",
                    "type": "C",
                    "urlSiteWeb": "",
                    "nomClubPro": "",
                    "engagements": [
                        {
                            "id": "eng1",
                            "idCompetition": {
                                "id": "comp1",
                                "nom": "Division 1",
                                "code": "D1",
                                "sexe": "M",
                                "competition_origine": "O",
                                "competition_origine_nom": "ON",
                                "competition_origine_niveau": 1,
                                "typeCompetition": "T",
                            },
                        }
                    ],
                }
            }
        )

        result = await client.get_equipes_async(organisme_id)
        assert result is not None
        assert len(result) == 1
        assert result[0].idCompetition is not None
        assert result[0].idCompetition.nom == "Division 1"


# ---------------------------------------------------------------------------
# Feature 3: search_rencontres_async with categorie filter
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_search_rencontres_async_with_categorie():
    """search_rencontres_async with categorie should filter hits client-side."""
    ms_client = MeilisearchFFBBClient(bearer_token="ms-token")
    api_client = ApiFFBBAppClient(bearer_token="api-token")
    facade = FFBBDataClient(api_client, ms_client)

    # The correct URL: MEILISEARCH_BASE_URL + MEILISEARCH_ENDPOINT_MULTI_SEARCH
    ms_url = "https://meilisearch-prod.ffbb.app/multi-search"

    with respx.mock:
        respx.post(ms_url).respond(
            json={
                "results": [
                    {
                        "indexUid": "ffbbserver_rencontres",
                        "hits": [
                            {
                                # ID must contain the query "Test" to satisfy RencontresHit.is_valid_for_query
                                "id": "match_Test_1",
                                "nomEquipe1": "Team A",
                                "nomEquipe2": "Team B",
                                "competitionId": {
                                    "id": "comp1",
                                    "nom": "Competition 1",
                                    "categorie": {
                                        "code": "U11M",
                                        "libelle": "U11 Masculin",
                                        "ordre": 1,
                                    },
                                },
                            },
                            {
                                "id": "match_Test_2",
                                "nomEquipe1": "Team C",
                                "nomEquipe2": "Team D",
                                "competitionId": {
                                    "id": "comp2",
                                    "nom": "Competition 2",
                                    "categorie": {
                                        "code": "U13M",
                                        "libelle": "U13 Masculin",
                                        "ordre": 2,
                                    },
                                },
                            },
                        ],
                        "estimatedTotalHits": 2,
                        "query": "Test",
                        "limit": 20,
                        "offset": 0,
                        "processingTimeMs": 10,
                    }
                ]
            }
        )

        # Filter by code
        result = await facade.search_rencontres_async(name="Test", categorie="U11M")
        assert result is not None
        assert len(result.hits) == 1
        assert result.hits[0].id == "match_Test_1"

    # Second call needs a separate respx.mock context (route was consumed)
    with respx.mock:
        respx.post(ms_url).respond(
            json={
                "results": [
                    {
                        "indexUid": "ffbbserver_rencontres",
                        "hits": [
                            {
                                "id": "match_Test_1",
                                "nomEquipe1": "Team A",
                                "nomEquipe2": "Team B",
                                "competitionId": {
                                    "id": "comp1",
                                    "nom": "Competition 1",
                                    "categorie": {
                                        "code": "U11M",
                                        "libelle": "U11 Masculin",
                                        "ordre": 1,
                                    },
                                },
                            },
                            {
                                "id": "match_Test_2",
                                "nomEquipe1": "Team C",
                                "nomEquipe2": "Team D",
                                "competitionId": {
                                    "id": "comp2",
                                    "nom": "Competition 2",
                                    "categorie": {
                                        "code": "U13M",
                                        "libelle": "U13 Masculin",
                                        "ordre": 2,
                                    },
                                },
                            },
                        ],
                        "estimatedTotalHits": 2,
                        "query": "Test",
                        "limit": 20,
                        "offset": 0,
                        "processingTimeMs": 10,
                    }
                ]
            }
        )

        # Filter by libelle
        result = await facade.search_rencontres_async(
            name="Test", categorie="U13 Masculin"
        )
        assert result is not None
        assert len(result.hits) == 1
        assert result.hits[0].id == "match_Test_2"


# ---------------------------------------------------------------------------
# Retry logic: successful after transient errors
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_lives_async_returns_empty_list():
    """get_lives_async should return [] for an empty JSON array response."""
    client = ApiFFBBAppClient(bearer_token="test-token")

    with respx.mock:
        respx.get("https://api.ffbb.app/json/lives.json").respond(json=[])

        lives = await client.get_lives_async()
        assert lives is not None
        assert lives == []


@pytest.mark.asyncio
async def test_get_lives_async_raises_on_server_error():
    """get_lives_async should expose a typed server failure."""
    client = ApiFFBBAppClient(bearer_token="test-token")

    with respx.mock:
        respx.get("https://api.ffbb.app/json/lives.json").respond(503)

        with pytest.raises(FFBBServerError, match="HTTP 503"):
            await client.get_lives_async()
