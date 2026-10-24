"""WAF circuit breaker and exact Meilisearch fallback."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ffbb_data_client.helpers import meilisearch_fallback as mf
from ffbb_data_client.utils import retry_utils
from ffbb_data_client.utils.retry_utils import (
    make_http_request_with_retry,
    make_http_request_with_retry_async,
    waf_blocked_hosts,
)

URL = "https://bo.ffbb.com/items/ffbbserver_saisons"


def _blocked() -> httpx.Response:
    return httpx.Response(
        403,
        headers={"content-type": "text/html"},
        content=b"<html><body>BunnyCDN-FR1</body></html>",
        request=httpx.Request("GET", URL),
    )


def test_waf_block_opens_circuit_and_skips_network() -> None:
    session = MagicMock()
    session.get.return_value = _blocked()

    first = make_http_request_with_retry("GET", URL, {}, cached_session=session)
    second = make_http_request_with_retry("GET", URL, {}, cached_session=session)

    assert first.status_code == second.status_code == 403
    assert session.get.call_count == 1
    assert "bo.ffbb.com" in waf_blocked_hosts()


def test_directus_json_403_does_not_open_circuit() -> None:
    session = MagicMock()
    session.get.return_value = httpx.Response(
        403,
        headers={"content-type": "application/json"},
        content=b'{"errors": []}',
        request=httpx.Request("GET", URL),
    )

    make_http_request_with_retry("GET", URL, {}, cached_session=session)

    assert waf_blocked_hosts() == {}


def test_circuit_half_opens_after_cooldown() -> None:
    session = MagicMock()
    session.get.return_value = _blocked()
    make_http_request_with_retry("GET", URL, {}, cached_session=session)

    with patch.object(retry_utils.time, "monotonic", return_value=1e12):
        make_http_request_with_retry("GET", URL, {}, cached_session=session)

    assert session.get.call_count == 2


def test_circuit_is_per_host() -> None:
    session = MagicMock()
    session.get.side_effect = [_blocked(), httpx.Response(200, json={})]
    make_http_request_with_retry("GET", URL, {}, cached_session=session)

    other = make_http_request_with_retry(
        "GET", "https://meilisearch-prod.ffbb.app/health", {}, cached_session=session
    )

    assert other.status_code == 200


@pytest.mark.asyncio
async def test_async_waf_block_opens_circuit() -> None:
    session = MagicMock()
    session.get = AsyncMock(return_value=_blocked())

    await make_http_request_with_retry_async("GET", URL, {}, cached_session=session)
    await make_http_request_with_retry_async("GET", URL, {}, cached_session=session)

    assert session.get.await_count == 1


@pytest.mark.asyncio
async def test_organisme_from_meilisearch_matches_exact_ids() -> None:
    org = {"id": "9326", "code": "ARA0063074", "nom": "SCBA"}
    engagements = [
        {"id": "1", "codeClub": "ARA0063074"},
        {"id": "2", "codeClub": "ARA0063010"},
    ]
    search = AsyncMock(side_effect=[[{"id": "93260"}, org], engagements])
    with patch.object(mf, "meili_search_async", search):
        result = await mf.organisme_from_meilisearch(9326)

    assert result is not None
    assert result["id"] == "9326"
    assert [e["id"] for e in result["engagements"]] == ["1"]
    assert search.await_args_list[1].args[1]["attributesToSearchOn"] == ["codeClub"]


@pytest.mark.asyncio
async def test_club_rencontres_uses_exact_code_filter() -> None:
    search = AsyncMock(return_value=[])
    with patch.object(mf, "meili_search_async", search):
        await mf.club_rencontres_from_meilisearch("ARA0063074")
        assert await mf.club_rencontres_from_meilisearch('X" OR id > 0') == []

    body = search.await_args.args[1]
    assert body["filter"] == (
        'idOrganismeEquipe1.code = "ARA0063074" '
        'OR idOrganismeEquipe2.code = "ARA0063074"'
    )
    assert search.await_count == 1
