from unittest.mock import AsyncMock, Mock, patch

import pytest
import respx

from ffbb_data_client.clients.api_ffbb_app_client import ApiFFBBAppClient


@pytest.mark.asyncio
async def test_get_lives_async():
    client = ApiFFBBAppClient(bearer_token="test-token", debug=True)

    with respx.mock:
        respx.get("https://api.ffbb.app/json/lives.json").respond(
            json=[
                {
                    "matchId": 1,
                    "competitionName": "Match 1",
                    "currentStatus": "en_cours",
                }
            ]
        )

        lives = await client.get_lives_async()
        assert lives is not None
        assert len(lives) == 1
        assert lives[0].match_id == 1
        assert lives[0].competition_name == "Match 1"


@pytest.mark.asyncio
async def test_get_competition_async():
    client = ApiFFBBAppClient(bearer_token="test-token", debug=True)

    with respx.mock:
        # Use a regex match to handle the complex query parameters
        respx.get(
            url__startswith="https://api.ffbb.app/items/ffbbserver_competitions/123"
        ).respond(
            json={
                "data": {
                    "id": "123",
                    "nom": "Coupe de France",
                    "sexe": "M",
                    "saison": "2025-2026",
                    "code": "CF",
                    "typeCompetition": "Coupe",
                    "liveStat": 0,
                    "competition_origine": "123",
                    "competition_origine_nom": "CF",
                    "publicationInternet": "O",
                }
            }
        )

        comp = await client.get_competition_async(123)
        assert comp is not None
        assert comp.id == "123"
        assert comp.nom == "Coupe de France"


@pytest.mark.asyncio
async def test_get_competition_async_reuses_client_async_session():
    custom_async_session = Mock()
    client = ApiFFBBAppClient(
        bearer_token="test-token",
        debug=True,
        async_cached_session=custom_async_session,
    )

    with patch(
        "ffbb_data_client.clients._mixins.competition.http_get_json_async",
        new=AsyncMock(return_value={"data": {"id": "123", "nom": "Coupe de France"}}),
    ) as mock_http_get_json_async:
        await client.get_competition_async(123)

    assert mock_http_get_json_async.call_count == 1
    assert (
        mock_http_get_json_async.call_args.kwargs["cached_session"]
        is custom_async_session
    )
