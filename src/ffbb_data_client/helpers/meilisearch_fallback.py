"""Requêtes Meilisearch exactes, utilisées quand Directus est coupé par le WAF BunnyCDN."""

from __future__ import annotations

import os
from typing import Any

from ..config import (
    DEFAULT_FALLBACK_MEILISEARCH_TOKEN,
    ENV_MEILISEARCH_TOKEN,
    MEILISEARCH_BASE_URL,
    MEILISEARCH_INDEX_COMPETITIONS,
    MEILISEARCH_INDEX_ENGAGEMENTS,
    MEILISEARCH_INDEX_ORGANISMES,
    MEILISEARCH_INDEX_RENCONTRES,
)
from .http_requests_utils import http_post_json_async

_POULE_TO_COMP_CACHE: dict[str, tuple[str, str]] = {}


def register_poule_competition(
    poule_id: int | str, competition_id: int | str, poule_nom: str = ""
) -> None:
    """Enregistre la correspondance poule_id -> (competition_id, poule_nom)."""
    pid = str(poule_id).strip()
    cid = str(competition_id).strip()
    if pid and cid:
        _POULE_TO_COMP_CACHE[pid] = (cid, str(poule_nom or "").strip())


async def meili_search_async(index: str, body: dict[str, Any]) -> list[dict[str, Any]]:
    base = (os.getenv("MEILISEARCH_URL") or MEILISEARCH_BASE_URL).rstrip("/")
    token = os.getenv(ENV_MEILISEARCH_TOKEN) or DEFAULT_FALLBACK_MEILISEARCH_TOKEN
    data = await http_post_json_async(
        f"{base}/indexes/{index}/search",
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        body,
        cached_session=None,
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
        matched_engs = [e for e in engagements if e.get("codeClub") == code]
        for e in matched_engs:
            p_obj = e.get("idPoule") or {}
            c_obj = e.get("idCompetition") or {}
            if isinstance(p_obj, dict) and isinstance(c_obj, dict):
                register_poule_competition(
                    p_obj.get("id") or "",
                    c_obj.get("id") or "",
                    p_obj.get("nom") or "",
                )
        org["engagements"] = matched_engs
    return org


async def competition_from_meilisearch(
    competition_id: int | str,
) -> dict[str, Any] | None:
    """Compétition reconstruite depuis l'index Meilisearch ffbbserver_competitions."""
    cid = str(competition_id).strip()
    if not cid:
        return None
    hits = await meili_search_async(
        MEILISEARCH_INDEX_COMPETITIONS,
        {"q": f'"{cid}"', "attributesToSearchOn": ["id"], "limit": 5},
    )
    comp = next((h for h in hits if str(h.get("id")) == cid), None)
    if not comp:
        return None
    for p in comp.get("poules") or []:
        if isinstance(p, dict) and p.get("id"):
            register_poule_competition(p["id"], cid, p.get("nom") or "")
    # Normaliser phases (liste de strings dans Meilisearch -> liste de dicts pour GetCompetitionResponse.from_dict)
    raw_phases = comp.get("phases")
    if isinstance(raw_phases, list) and any(
        not isinstance(ph, dict) for ph in raw_phases
    ):
        comp = dict(comp)
        comp["phases"] = []
    if isinstance(comp.get("saison"), dict):
        comp = dict(comp)
        comp["saison"] = comp["saison"].get("code") or str(
            comp["saison"].get("id") or ""
        )
    return comp


async def poule_from_meilisearch(
    poule_id: int | str,
    competition_id: int | str | None = None,
) -> dict[str, Any] | None:
    """Reconstitue une poule (équipes engagées et rencontres) depuis Meilisearch."""
    pid = str(poule_id).strip()
    if not pid:
        return None

    cached_meta = _POULE_TO_COMP_CACHE.get(pid)
    cid = (
        str(competition_id).strip()
        if competition_id
        else (cached_meta[0] if cached_meta else "")
    )
    poule_nom = cached_meta[1] if cached_meta else ""

    comp_hit: dict[str, Any] | None = None
    poule_entry: dict[str, Any] | None = None

    if cid:
        comp_hit = await competition_from_meilisearch(cid)
        if comp_hit:
            for p in comp_hit.get("poules") or []:
                if isinstance(p, dict) and str(p.get("id")) == pid:
                    poule_entry = p
                    poule_nom = p.get("nom") or poule_nom
                    break

    if not cid and not poule_entry:
        return None

    rencontres_raw: list[dict[str, Any]] = []
    if cid and poule_nom:
        safe_nom = poule_nom.replace('"', '\\"')
        rencontres_raw = await meili_search_async(
            MEILISEARCH_INDEX_RENCONTRES,
            {
                "q": "",
                "filter": f'competitionId.id = "{cid}" AND idPoule.nom = "{safe_nom}"',
                "limit": 500,
            },
        )
    elif cid:
        all_comp_r = await meili_search_async(
            MEILISEARCH_INDEX_RENCONTRES,
            {
                "q": "",
                "filter": f'competitionId.id = "{cid}"',
                "limit": 500,
            },
        )
        rencontres_raw = [
            r for r in all_comp_r if str((r.get("idPoule") or {}).get("id")) == pid
        ]

    rencontres: list[dict[str, Any]] = []
    for r in rencontres_raw:
        if not isinstance(r, dict):
            continue
        if str((r.get("idPoule") or {}).get("id") or pid) != pid:
            continue
        rencontres.append(
            {
                "id": str(r.get("id") or ""),
                "numero": str(r.get("numero") or ""),
                "numeroJournee": str(r.get("numeroJournee") or ""),
                "idPoule": pid,
                "competitionId": cid,
                "resultatEquipe1": str(r.get("resultatEquipe1") or ""),
                "resultatEquipe2": str(r.get("resultatEquipe2") or ""),
                "joue": 1 if r.get("joue") in (True, 1, "1") else 0,
                "nomEquipe1": str(r.get("nomEquipe1") or ""),
                "nomEquipe2": str(r.get("nomEquipe2") or ""),
                "date_rencontre": str(
                    r.get("date_rencontre") or r.get("date") or "1970-01-01"
                ),
            }
        )

    classements: list[dict[str, Any]] = []
    engagements = (poule_entry or {}).get("engagements") or []
    for idx, eng in enumerate(engagements, start=1):
        if not isinstance(eng, dict):
            continue
        classements.append(
            {
                "id": f"{pid}_{idx}",
                "position": idx,
                "idEngagement": {
                    "id": str(eng.get("id") or ""),
                    "nom": str(eng.get("nom") or ""),
                },
                "organisme": {
                    "id": "",
                    "nom": str(eng.get("nom") or ""),
                },
                "idCompetition": cid,
                "idPoule": {"id": pid},
                "points": 0,
                "matchJoues": 0,
                "gagnes": 0,
                "perdus": 0,
                "paniersMarques": 0,
                "paniersEncaisses": 0,
                "difference": 0,
                "quotient": 0.0,
            }
        )

    return {
        "id": pid,
        "nom": poule_nom or f"Poule {pid}",
        "rencontres": rencontres,
        "classements": classements,
    }


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
