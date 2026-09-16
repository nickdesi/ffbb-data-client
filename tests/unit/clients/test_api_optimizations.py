import time
from datetime import datetime

import httpx
import pytest

from ffbb_data_client.models.get_poule_response import GetPouleResponse
from ffbb_data_client.models.team_ranking import TeamRanking

pytest.importorskip("fastapi")

from ffbb_data_client.api import (  # noqa: E402
    LRUCache,
    _salle_cache,
    app,
    resolve_exact_salle_address,
)


def test_lru_cache_eviction_and_access():
    cache = LRUCache(maxsize=2)
    cache["x"] = 10
    cache["y"] = 20
    assert "x" in cache
    assert cache["y"] == 20

    # Access x so y becomes least recently used
    _ = cache["x"]

    # Insert z -> y must be evicted
    cache["z"] = 30
    assert "x" in cache
    assert "z" in cache
    assert "y" not in cache
    assert cache.get("y") is None


def test_lru_cache_ttl_expiration():
    # Cache with very short TTL of 0.05s
    cache = LRUCache(maxsize=10, default_ttl=0.05)
    cache["key1"] = "hello"
    assert "key1" in cache
    assert cache["key1"] == "hello"

    time.sleep(0.06)
    # Key must be expired and pruned
    assert "key1" not in cache
    assert cache.get("key1") is None


def test_salle_cache_mutualization():
    _salle_cache["salle_888"] = (
        "Gymnase Central, Rue de la Paix, 63000 Clermont-Ferrand"
    )
    # Even if org_id is different or not specified, query with salle_id=888 should hit mutualized cache
    res1 = resolve_exact_salle_address(None, salle_id=888, org_id=123)
    assert res1 == "Gymnase Central, Rue de la Paix, 63000 Clermont-Ferrand"

    res2 = resolve_exact_salle_address(None, salle_id="888", org_id=999)
    assert res2 == "Gymnase Central, Rue de la Paix, 63000 Clermont-Ferrand"


def test_get_poule_response_classement_alias():
    ranking = TeamRanking(id="1", organisme_nom="SCBA", position=1, points=10)
    poule = GetPouleResponse(
        id="999",
        nom="Poule Haute",
        rencontres=[],
        classements=[ranking],
    )
    assert poule.classements is not None
    assert poule.classement is not None
    assert len(poule.classement) == 1
    assert poule.classement[0].organisme_nom == "SCBA"


@pytest.mark.asyncio
async def test_health_endpoint_utc_timestamp():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ffbb-data-client-api"
        dt = datetime.fromisoformat(data["timestamp"])
        assert dt is not None
        assert dt.tzinfo is not None
