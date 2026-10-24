"""Requêtes Meilisearch exactes, utilisées quand Directus est coupé par le WAF BunnyCDN."""

from __future__ import annotations

import os
from typing import Any

from ..config import (
    DEFAULT_FALLBACK_MEILISEARCH_TOKEN,
    ENV_MEILISEARCH_TOKEN,
    MEILISEARCH_BASE_URL,
    MEILISEARCH_INDEX_ENGAGEMENTS,
    MEILISEARCH_INDEX_ORGANISMES,
    MEILISEARCH_INDEX_RENCONTRES,
)
from .http_requests_utils import http_post_json_async


async def meili_search_async(index: str, body: dict[str, Any]) -> list[dict[str, Any]]:
    base = (os.getenv("MEILISEARCH_URL") or MEILISEARCH_BASE_URL).rstrip("/")
    token = os.getenv(ENV_MEILISEARCH_TOKEN) or DEFAULT_FALLBACK_MEILISEARCH_TOKEN
    data = await http_post_json_async(
        f"{base}/indexes/{index}/search",
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        body,
    )
    hits = data.get("hits") if isinstance(data, dict) else None
    return hits if isinstance(hits, list) else []


async def organisme_from_meilisearch(
    organisme_id: int | str,
) -> dict[str, Any] | None:
    """Organisme et ses engagements, appariés sur `id` et `codeClub` exacts."""
    oid = str(organisme_id).strip()
    hits = await meili_search_async(
        MEILISEARCH_INDEX_ORGANISMES,
        {"q": f'"{oid}"', "attributesToSearchOn": ["id"], "limit": 5},
    )
    org = next((h for h in hits if str(h.get("id")) == oid), None)
    code = org.get("code") if org else None
    if org and code:
        engagements = await meili_search_async(
            MEILISEARCH_INDEX_ENGAGEMENTS,
            {"q": f'"{code}"', "attributesToSearchOn": ["codeClub"], "limit": 1000},
        )
        org["engagements"] = [e for e in engagements if e.get("codeClub") == code]
    return org


async def club_rencontres_from_meilisearch(club_code: str) -> list[dict[str, Any]]:
    """Rencontres du club. L'index ne couvre qu'une fenêtre glissante (~2 semaines)."""
    if not club_code.isalnum():
        return []
    return await meili_search_async(
        MEILISEARCH_INDEX_RENCONTRES,
        {
            "q": "",
            "filter": (
                f'idOrganismeEquipe1.code = "{club_code}" '
                f'OR idOrganismeEquipe2.code = "{club_code}"'
            ),
            "limit": 1000,
        },
    )
