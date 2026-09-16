"""Tests for v4 features: get_club_contacts_async, aiter_all_* streaming generators, and NiveauExtractor exports."""

import httpx
import pytest
import respx

from ffbb_data_client import (
    CategorieType,
    FFBBDataClient,
    NiveauExtractor,
    NiveauType,
)
from ffbb_data_client.clients.api_ffbb_app_client import ApiFFBBAppClient
from ffbb_data_client.clients.meilisearch_ffbb_client import MeilisearchFFBBClient


# ---------------------------------------------------------------------------
# Test 1: get_club_contacts_async
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_club_contacts_async():
    """get_club_contacts_async should fetch organisme and return structured ClubContacts."""
    api_client = ApiFFBBAppClient(bearer_token="test-token")
    ms_client = MeilisearchFFBBClient(bearer_token="test-token")
    client = FFBBDataClient(api_client, ms_client)
    organisme_id = 12345

    with respx.mock:
        respx.get(
            url__startswith=f"https://api.ffbb.app/items/ffbbserver_organismes/{organisme_id}"
        ).respond(
            json={
                "data": {
                    "id": str(organisme_id),
                    "nom": "BASKET CLUB CLERMONTOIS",
                    "code": "ARA0063001",
                    "mail": "contact@basket-clermont.fr",
                    "telephone": "0473000000",
                    "adresse": "12 RUE DU BASKET",
                    "membres": [
                        {
                            "id": "m1",
                            "nom": "DUPONT",
                            "prenom": "JEAN",
                            "codeFonction": "PRESI",
                            "mail": "president@basket-clermont.fr",
                            "telephoneFixe": "0600000001",
                        }
                    ],
                }
            }
        )

        contacts = await client.get_club_contacts_async(organisme_id)
        assert contacts is not None
        assert contacts.organisme is not None
        assert contacts.organisme.nom == "BASKET CLUB CLERMONTOIS"
        assert contacts.club_contact is not None
        assert contacts.club_contact.email == "contact@basket-clermont.fr"
        assert len(contacts.membres) == 1
        assert contacts.membres[0].role == "PRESI"
        assert contacts.membres[0].nom == "Dupont"
        assert contacts.membres[0].prenom == "Jean"


# ---------------------------------------------------------------------------
# Test 2: aiter_all_rencontres streaming generator
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_aiter_all_rencontres_streaming():
    """aiter_all_rencontres should stream rencontres across pages with proper termination."""
    api_client = ApiFFBBAppClient(bearer_token="test-token")
    ms_client = MeilisearchFFBBClient(bearer_token="test-token")
    client = FFBBDataClient(api_client, ms_client)

    with respx.mock:
        # Route handler for paginated rencontres
        def rencontres_callback(request):
            params = dict(request.url.params)
            offset = int(params.get("offset", "0"))
            limit = int(params.get("limit", "2"))

            all_data = [
                {"id": "r1", "nom": "Match 1", "numero": "101"},
                {"id": "r2", "nom": "Match 2", "numero": "102"},
                {"id": "r3", "nom": "Match 3", "numero": "103"},
            ]
            page_data = all_data[offset : offset + limit]
            return httpx.Response(200, json={"data": page_data})

        respx.get(
            url__startswith="https://api.ffbb.app/items/ffbbserver_rencontres"
        ).mock(side_effect=rencontres_callback)

        results = []
        async for rencontre in client.aiter_all_rencontres(page_size=2, max_items=10):
            results.append(rencontre)

        assert len(results) == 3
        assert results[0].id == "r1"
        assert results[1].id == "r2"
        assert results[2].id == "r3"


# ---------------------------------------------------------------------------
# Test 3: aiter_all_salles with early break
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_aiter_all_salles_early_break():
    """aiter_all_salles should support early loop breaking without fetching excess pages."""
    api_client = ApiFFBBAppClient(bearer_token="test-token")
    ms_client = MeilisearchFFBBClient(bearer_token="test-token")
    client = FFBBDataClient(api_client, ms_client)

    with respx.mock:
        respx.get(
            url__startswith="https://api.ffbb.app/items/ffbbserver_salles"
        ).respond(
            json={
                "data": [
                    {"id": "s1", "libelle": "Gymnase A"},
                    {"id": "s2", "libelle": "Gymnase B"},
                    {"id": "s3", "libelle": "Gymnase C"},
                ]
            }
        )

        results = []
        async for salle in client.aiter_all_salles(page_size=10):
            results.append(salle)
            if len(results) == 1:
                break

        assert len(results) == 1
        assert results[0].libelle == "Gymnase A"


# ---------------------------------------------------------------------------
# Test 4: NiveauExtractor Exports and Logic
# ---------------------------------------------------------------------------
def test_niveau_extractor_exports_and_detection():
    """NiveauExtractor should properly extract levels and categories."""
    info_u13 = NiveauExtractor.extract_niveau("U13 MASCULIN RÉGIONALE 2 - POULE A")
    assert info_u13 is not None
    assert info_u13.type == NiveauType.REGIONAL
    assert info_u13.division == 2
    assert info_u13.categorie == CategorieType.U13

    info_senior_d1 = NiveauExtractor.extract_niveau(
        "DÉPARTEMENTALE MASCULINE SENIORS - DIVISION 1"
    )
    assert info_senior_d1 is not None
    assert info_senior_d1.type == NiveauType.DEPARTEMENTAL
    assert info_senior_d1.division == 1
    assert info_senior_d1.categorie == CategorieType.SENIORS
