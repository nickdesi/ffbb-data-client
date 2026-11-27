"""Requêtes Meilisearch exactes, utilisées quand Directus est coupé par le WAF BunnyCDN."""

from __future__ import annotations

import hashlib
import html as html_lib
import os
import re
import time
from typing import Any

import httpx

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
_SPORTSREGIONS_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_SPORTSREGIONS_TTL_S = 900.0
_SR_TABLE_RE = re.compile(r"<table[^>]*>(.*?)</table>", re.S | re.I)
_SR_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_SR_CELL_RE = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.S | re.I)
_SR_TAG_RE = re.compile(r"<[^>]+>")
_SR_DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _norm_team(name: str) -> str:
    return " ".join(str(name or "").upper().split())


async def fetch_sportsregions_poule_rencontres(
    poule_id: str,
    competition_id: str = "",
) -> list[dict[str, Any]]:
    """Récupère l'ensemble des journées (J1..Jn) d'une poule via la passerelle SportsRegions."""
    if os.getenv("FFBB_ENABLE_SPORTSREGIONS", "1").lower() in ("0", "false", "no"):
        return []
    pid = str(poule_id).strip()
    if not pid.isdigit():
        return []

    now = time.monotonic()
    cached = _SPORTSREGIONS_CACHE.get(pid)
    if cached and (now - cached[0]) < _SPORTSREGIONS_TTL_S:
        return [dict(item) for item in cached[1]]

    base_url = os.getenv(
        "FFBB_SPORTSREGIONS_BASE_URL", "https://www.gerzatbasket.com"
    ).rstrip("/")
    url = f"{base_url}/ffbb/poules/{pid}"
    try:
        async with httpx.AsyncClient(
            timeout=5.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ffbb-data-client/1.0)"},
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            page_html = resp.text
    except Exception:
        return []

    tables = _SR_TABLE_RE.findall(page_html)
    if not tables:
        return []

    parsed: list[dict[str, Any]] = []
    current_date_iso = "1970-01-01"
    for row_html in _SR_ROW_RE.findall(tables[0]):
        raw_cells = _SR_CELL_RE.findall(row_html)
        cells = [
            " ".join(html_lib.unescape(_SR_TAG_RE.sub(" ", c)).split())
            for c in raw_cells
        ]
        if len(cells) == 1:
            m_date = _SR_DATE_RE.match(cells[0])
            if m_date:
                dd, mm, yyyy = m_date.groups()
                current_date_iso = f"{yyyy}-{mm}-{dd}"
            continue
        if len(cells) >= 6 and cells[1].isdigit():
            jour = cells[1]
            t1 = cells[2]
            s1 = cells[3]
            s2 = cells[4]
            t2 = cells[5]
            if not t1 or not t2:
                continue
            joue = 1 if (s1.isdigit() and s2.isdigit()) else 0
            sig = hashlib.sha256(
                f"{pid}:{jour}:{_norm_team(t1)}:{_norm_team(t2)}".encode()
            ).hexdigest()[:12]
            parsed.append(
                {
                    "id": f"sr_{pid}_{sig}",
                    "numero": "",
                    "numeroJournee": jour,
                    "idPoule": pid,
                    "competitionId": competition_id,
                    "resultatEquipe1": s1 if joue else "",
                    "resultatEquipe2": s2 if joue else "",
                    "joue": joue,
                    "nomEquipe1": t1,
                    "nomEquipe2": t2,
                    "logoEquipe1": "",
                    "logoEquipe2": "",
                    "date_rencontre": f"{current_date_iso}T00:00:00",
                }
            )

    if parsed:
        _SPORTSREGIONS_CACHE[pid] = (now, parsed)
    return [dict(item) for item in parsed]


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
        {"q": cid, "attributesToSearchOn": ["id"], "limit": 50},
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

    rencontres: list[dict[str, Any]] = []
    if not cid and not poule_entry:
        sr_only = await fetch_sportsregions_poule_rencontres(pid)
        if not sr_only:
            return None
        rencontres = sr_only
    else:
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

        for r in rencontres_raw:
            if not isinstance(r, dict):
                continue
            p_obj = r.get("idPoule") or {}
            p_id = str(p_obj.get("id") if isinstance(p_obj, dict) else p_obj or "")
            if p_id and p_id != pid:
                continue
            if not poule_nom and isinstance(p_obj, dict) and p_obj.get("nom"):
                poule_nom = str(p_obj.get("nom"))

            org1 = r.get("idOrganismeEquipe1") or {}
            org2 = r.get("idOrganismeEquipe2") or {}
            logo1 = (
                (org1.get("logo") or {}).get("id")
                if isinstance(org1, dict) and isinstance(org1.get("logo"), dict)
                else (org1.get("logo") if isinstance(org1, dict) else "")
            )
            logo2 = (
                (org2.get("logo") or {}).get("id")
                if isinstance(org2, dict) and isinstance(org2.get("logo"), dict)
                else (org2.get("logo") if isinstance(org2, dict) else "")
            )

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
                    "logoEquipe1": str(logo1 or ""),
                    "logoEquipe2": str(logo2 or ""),
                    "date_rencontre": str(
                        r.get("date_rencontre") or r.get("date") or "1970-01-01"
                    ),
                }
            )

        # Enrichissement SportsRegions : récupère les journées hors fenêtre glissante Meilisearch (J1, J2, J5, J6...)
        sr_rencontres = await fetch_sportsregions_poule_rencontres(pid, cid)
        if sr_rencontres:
            by_key: dict[tuple[str, str, str], dict[str, Any]] = {
                (
                    str(m.get("numeroJournee") or ""),
                    _norm_team(m.get("nomEquipe1") or ""),
                    _norm_team(m.get("nomEquipe2") or ""),
                ): m
                for m in rencontres
            }
            for sr_m in sr_rencontres:
                key = (
                    str(sr_m.get("numeroJournee") or ""),
                    _norm_team(sr_m.get("nomEquipe1") or ""),
                    _norm_team(sr_m.get("nomEquipe2") or ""),
                )
                existing = by_key.get(key)
                if existing is None:
                    rencontres.append(sr_m)
                    by_key[key] = sr_m
                elif existing.get("joue") == 0 and sr_m.get("joue") == 1:
                    existing["joue"] = 1
                    existing["resultatEquipe1"] = sr_m["resultatEquipe1"]
                    existing["resultatEquipe2"] = sr_m["resultatEquipe2"]

    rencontres.sort(
        key=lambda m: (
            (
                int(m["numeroJournee"])
                if str(m.get("numeroJournee") or "").isdigit()
                else 999
            ),
            str(m.get("date_rencontre") or ""),
        )
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

    # Calculer les statistiques réelles depuis les rencontres jouées de la poule
    teams_stats: dict[str, dict[str, Any]] = {}
    for r in rencontres:
        for k in ["nomEquipe1", "nomEquipe2"]:
            name = r.get(k)
            if name and name not in teams_stats:
                teams_stats[name] = {
                    "nom": name,
                    "matchJoues": 0,
                    "gagnes": 0,
                    "perdus": 0,
                    "points": 0,
                    "paniersMarques": 0,
                    "paniersEncaisses": 0,
                }
        if r.get("joue") == 1:
            try:
                s1 = int(r.get("resultatEquipe1", 0) or 0)
                s2 = int(r.get("resultatEquipe2", 0) or 0)
                t1 = r.get("nomEquipe1")
                t2 = r.get("nomEquipe2")
                if t1 and t2 and (s1 > 0 or s2 > 0):
                    teams_stats[t1]["matchJoues"] += 1
                    teams_stats[t2]["matchJoues"] += 1
                    teams_stats[t1]["paniersMarques"] += s1
                    teams_stats[t1]["paniersEncaisses"] += s2
                    teams_stats[t2]["paniersMarques"] += s2
                    teams_stats[t2]["paniersEncaisses"] += s1
                    if s1 > s2:
                        teams_stats[t1]["gagnes"] += 1
                        teams_stats[t1]["points"] += 2
                        teams_stats[t2]["perdus"] += 1
                        teams_stats[t2]["points"] += 1
                    elif s2 > s1:
                        teams_stats[t2]["gagnes"] += 1
                        teams_stats[t2]["points"] += 2
                        teams_stats[t1]["perdus"] += 1
                        teams_stats[t1]["points"] += 1
            except (ValueError, TypeError):
                # Scores illisibles (données Meilisearch partielles) : la
                # rencontre est exclue du calcul du classement.
                pass

    if classements and teams_stats:
        norm_stats = {
            " ".join(k.upper().split()): v for k, v in teams_stats.items() if k
        }
        for c in classements:
            c_nom = " ".join(
                str((c.get("organisme") or {}).get("nom") or "").upper().split()
            )
            st = norm_stats.get(c_nom)
            if not st and c_nom:
                for k_norm, v in norm_stats.items():
                    if c_nom in k_norm or k_norm in c_nom:
                        st = v
                        break
            if st:
                diff = st["paniersMarques"] - st["paniersEncaisses"]
                quot = (
                    round(st["paniersMarques"] / st["paniersEncaisses"], 3)
                    if st["paniersEncaisses"] > 0
                    else 0.0
                )
                c.update(
                    {
                        "points": st["points"],
                        "matchJoues": st["matchJoues"],
                        "gagnes": st["gagnes"],
                        "perdus": st["perdus"],
                        "paniersMarques": st["paniersMarques"],
                        "paniersEncaisses": st["paniersEncaisses"],
                        "difference": diff,
                        "quotient": quot,
                    }
                )
        classements.sort(
            key=lambda x: (
                int(x.get("points") or 0),
                int(x.get("difference") or 0),
                int(x.get("paniersMarques") or 0),
            ),
            reverse=True,
        )
        for idx, c in enumerate(classements, start=1):
            c["position"] = idx

    # Si le tableau de bord n'a pas pu récupérer les engagements officiels depuis la compétition,
    # on déduit les équipes et classements directement depuis les rencontres de la poule.
    if not classements and rencontres:
        sorted_teams = sorted(
            teams_stats.values(),
            key=lambda x: (x["points"], x["paniersMarques"] - x["paniersEncaisses"]),
            reverse=True,
        )
        for idx, t in enumerate(sorted_teams, start=1):
            diff = t["paniersMarques"] - t["paniersEncaisses"]
            quot = (
                round(t["paniersMarques"] / t["paniersEncaisses"], 3)
                if t["paniersEncaisses"] > 0
                else 0.0
            )
            classements.append(
                {
                    "id": f"{pid}_{idx}",
                    "position": idx,
                    "idEngagement": {
                        "id": f"meili_{pid}_{idx}",
                        "nom": t["nom"],
                    },
                    "organisme": {
                        "id": "",
                        "nom": t["nom"],
                    },
                    "idCompetition": cid,
                    "idPoule": {"id": pid},
                    "points": t["points"],
                    "matchJoues": t["matchJoues"],
                    "gagnes": t["gagnes"],
                    "perdus": t["perdus"],
                    "paniersMarques": t["paniersMarques"],
                    "paniersEncaisses": t["paniersEncaisses"],
                    "difference": diff,
                    "quotient": quot,
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
