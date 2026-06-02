"""
Tests pour les méthodes de Cache Warming de FFBBDataClient.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from ffbb_data_client import FFBBDataClient
from ffbb_data_client.models.get_competition_response import GetCompetitionResponse


@pytest.mark.asyncio
async def test_warm_organisme_cache_async():
    client = FFBBDataClient.create(
        meilisearch_bearer_token="test-mls-token",
        api_bearer_token="test-api-token",
        debug=False,
    )

    with patch.object(
        client, "get_organisme_async", new_callable=AsyncMock
    ) as mock_get_org, patch.object(
        client, "get_equipes_async", new_callable=AsyncMock
    ) as mock_get_eq:

        await client.warm_organisme_cache_async(1234, max_concurrency=2)

        mock_get_org.assert_called_once_with(1234)
        mock_get_eq.assert_called_once_with(1234)


def test_warm_organisme_cache():
    client = FFBBDataClient.create(
        meilisearch_bearer_token="test-mls-token",
        api_bearer_token="test-api-token",
        debug=False,
    )

    with patch.object(
        client, "warm_organisme_cache_async", new_callable=AsyncMock
    ) as mock_warm_async:

        client.warm_organisme_cache(1234, max_concurrency=2)
        mock_warm_async.assert_called_once_with(1234, 2)


@pytest.mark.asyncio
async def test_warm_competition_cache_async():
    client = FFBBDataClient.create(
        meilisearch_bearer_token="test-mls-token",
        api_bearer_token="test-api-token",
        debug=False,
    )

    mock_comp = MagicMock(spec=GetCompetitionResponse)
    mock_comp.id = "5678"
    mock_comp.nom = "Nationale 1"

    poule1 = MagicMock()
    poule1.id = "111"
    poule2 = MagicMock()
    poule2.id = "222"
    mock_comp.poules = [poule1, poule2]

    phase1 = MagicMock()
    poule3 = MagicMock()
    poule3.id = "333"
    phase1.poules = [poule3]
    mock_comp.phases = [phase1]

    with patch.object(
        client, "get_competition_async", new=AsyncMock(return_value=mock_comp)
    ) as mock_get_comp, patch.object(
        client, "get_poule_async", new_callable=AsyncMock
    ) as mock_get_poule:

        await client.warm_competition_cache_async(5678, max_concurrency=3)

        mock_get_comp.assert_called_once_with(5678)
        assert mock_get_poule.call_count == 3
        called_ids = {call.args[0] for call in mock_get_poule.call_args_list}
        assert called_ids == {111, 222, 333}


def test_warm_competition_cache():
    client = FFBBDataClient.create(
        meilisearch_bearer_token="test-mls-token",
        api_bearer_token="test-api-token",
        debug=False,
    )

    with patch.object(
        client, "warm_competition_cache_async", new_callable=AsyncMock
    ) as mock_warm_async:

        client.warm_competition_cache(5678, max_concurrency=3)
        mock_warm_async.assert_called_once_with(5678, 3)
