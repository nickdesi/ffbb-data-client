"""
FastAPI REST API for FFBB Data Client.
Provides public HTTP endpoints, Swagger documentation at /docs,
and hosts the official documentation website at /.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .clients.ffbb_data_client import FFBBDataClient

# Directories
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_WEBSITE_DIR = _BASE_DIR / "website"
if not _WEBSITE_DIR.exists():
    _WEBSITE_DIR = Path("/app/website")

app = FastAPI(
    title="FFBB Data Client API",
    description="API REST moderne & asynchrone pour les données officielles de la Fédération Française de BasketBall.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Client Singleton
_client: Optional[FFBBDataClient] = None


def get_client() -> FFBBDataClient:
    global _client
    if _client is None:
        _client = FFBBDataClient.create()
    return _client


WEEKDAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MONTHS_FR = [
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]


def format_french_date(iso_str: str) -> str:
    """Formats 'YYYY-MM-DD' into French readable string 'Samedi 12 Décembre 2026'."""
    if not iso_str:
        return ""
    try:
        parts = iso_str.split("-")
        if len(parts) != 3:
            return iso_str
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        dt = datetime(y, m, d)
        weekday = WEEKDAYS_FR[dt.weekday()]
        return f"{weekday} {d} {MONTHS_FR[m - 1]} {y}"
    except Exception:
        return iso_str


def normalize_team_name(team_raw: str, comp_name: str = "") -> str:
    raw = (team_raw or "").upper().strip()
    comp = (comp_name or "").upper().strip()

    m_cat = re.search(r"U\s*(\d+)", raw) or re.search(r"U\s*(\d+)", comp)
    if m_cat:
        cat = m_cat.group(1)
        m_num = re.search(r"[- ](\d+)$", raw)
        num = m_num.group(1) if m_num else "1"
        return f"U{cat} M{num}"

    m_num = re.search(r"[- ](\d+)$", raw)
    num = m_num.group(1) if m_num else None

    if not num:
        if "RM2" in comp or "DIVISION 2" in comp:
            num = "2"
        elif "RM3" in comp or "DIVISION 3" in comp:
            num = "3"
        elif "PNM" in comp or "PRE NATIONALE" in comp or "PRÉ NATIONALE" in comp:
            num = "1"
        else:
            num = "1"

    return f"SENIOR M{num}"


def clean_opponent_name(opp_raw: str) -> str:
    if not opp_raw:
        return "Adversaire Inconnu"
    cleaned = opp_raw.strip()
    cleaned = re.sub(r"^(IE\s*[-]?\s*|CTC\s*[-]?\s*)", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


# Cache dictionaries
_org_cache: dict[int, Any] = {}
_logo_cache: dict[str, Optional[str]] = {}
_salle_cache: dict[str, str] = {}


def get_cached_organisme(client, org_id: Any):
    if not org_id:
        return None
    try:
        oid = int(org_id)
    except Exception:
        return None
    if oid in _org_cache:
        return _org_cache[oid]
    try:
        org = client.get_organisme(oid)
        _org_cache[oid] = org
        return org
    except Exception:
        _org_cache[oid] = None
        return None


def resolve_exact_salle_address(client, salle_id: Any, org_id: Any, default_name: str = "") -> str:
    """Résout l'adresse complète officielle de la salle (Nom - Rue, CP Ville)."""
    sid = str(salle_id) if salle_id else ""
    org_key = str(org_id) if org_id else ""
    cache_key = f"{sid}_{org_key}"

    if cache_key in _salle_cache:
        return _salle_cache[cache_key]

    org = get_cached_organisme(client, org_id) if org_id else None

    # 1. Vérifier si la salle principale de l'organisme hôte correspond
    if org and getattr(org, 'salle', None):
        o_salle = org.salle
        o_sid = str(getattr(o_salle, 'id', ''))
        if o_sid == sid or not sid:
            nom = getattr(o_salle, 'libelle', '') or getattr(o_salle, 'nom', '') or default_name
            adr = getattr(o_salle, 'adresse', '') or ""
            commune = getattr(o_salle, 'commune', None)
            cp = getattr(commune, 'codePostal', '') or getattr(commune, 'code_postal', '') if commune else ""
            v = getattr(commune, 'libelle', '') or getattr(o_salle, 'ville', '') if commune else ""
            parts = [adr, f"{cp} {v}".strip()]
            full_addr = ", ".join([p for p in parts if p])
            full = f"{nom} - {full_addr}" if nom and full_addr else (nom or full_addr)
            if full:
                _salle_cache[cache_key] = full
                return full

    # 2. Résolution de la salle spécifique + recherche de la commune via Meilisearch
    if sid:
        try:
            salle = client.get_salle(sid)
            if salle:
                nom = getattr(salle, 'libelle', '') or getattr(salle, 'nom', '') or default_name
                adr = getattr(salle, 'adresse', '') or ""
                cp, v = "", ""
                try:
                    res = client.search_salles(nom)
                    if res and getattr(res, 'hits', None):
                        matched_hit = None
                        for hit in res.hits:
                            if str(getattr(hit, 'id', '')) == sid:
                                matched_hit = hit
                                break
                        if not matched_hit:
                            matched_hit = res.hits[0]
                        commune = getattr(matched_hit, 'commune', None)
                        if commune:
                            cp = getattr(commune, 'code_postal', '') or getattr(commune, 'codePostal', '') or ""
                            v = getattr(commune, 'libelle', '') or ""
                except Exception:
                    pass

                parts = [adr, f"{cp} {v}".strip()]
                full_addr = ", ".join([p for p in parts if p])
                full = f"{nom} - {full_addr}" if nom and full_addr else (nom or full_addr)
                if full:
                    _salle_cache[cache_key] = full
                    return full
        except Exception:
            pass

    return default_name or "Lieu à confirmer"


@app.get("/health", tags=["Monitoring"])
async def health():
    return {
        "status": "healthy",
        "service": "ffbb-data-client-api",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/v1/club/{organisme_id}/matches", tags=["Clubs"])
async def get_club_matches(
    organisme_id: int,
    team: Optional[str] = Query(None, description="Filtrer par équipe (ex: 'SENIOR M1', 'U18 M1', 'ALL')"),
):
    """
    Récupère l'ensemble des rencontres officielles FFBB d'un club,
    avec détection domicile/extérieur, calcul des équipes, salles résolues avec adresse exacte et logos officiels.
    """
    client = get_client()

    try:
        org = client.get_organisme(organisme_id)
        if not org:
            raise HTTPException(status_code=404, detail=f"Club {organisme_id} introuvable.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur FFBB: {e}")

    club_name = getattr(org, "nom", "") or "Club"
    club_logo_url: Optional[str] = None
    if getattr(org, "logo", None):
        logo_id = getattr(org.logo, "id", None) or org.logo
        if logo_id:
            club_logo_url = f"https://api.ffbb.com/assets/{logo_id}"

    engagements = getattr(org, "engagements", []) or []
    candidate_matches = []
    seen_match_ids: set[str] = set()

    for eng in engagements:
        poule_obj = getattr(eng, "idPoule", None)
        comp_obj = getattr(eng, "idCompetition", None)
        poule_id = getattr(poule_obj, "id", None) or (str(poule_obj) if poule_obj else None)
        comp_nom = getattr(comp_obj, "nom", "") or ""

        if not poule_id:
            continue

        try:
            poule = client.get_poule(int(poule_id))
            rencontres = getattr(poule, "rencontres", []) or []
        except Exception:
            continue

        for m in rencontres:
            m_id = str(getattr(m, "id", "") or "")
            if not m_id or m_id in seen_match_ids:
                continue

            nom_eq1 = getattr(m, "nomEquipe1", "") or ""
            nom_eq2 = getattr(m, "nomEquipe2", "") or ""
            id_org1 = str(getattr(m, "idOrganismeEquipe1", "") or "")
            id_org2 = str(getattr(m, "idOrganismeEquipe2", "") or "")

            is_club1 = id_org1 == str(organisme_id) or club_name.upper() in nom_eq1.upper()
            is_club2 = id_org2 == str(organisme_id) or club_name.upper() in nom_eq2.upper()

            if not is_club1 and not is_club2:
                continue

            seen_match_ids.add(m_id)
            candidate_matches.append((m_id, comp_nom, is_club1, is_club2))

    from concurrent.futures import ThreadPoolExecutor

    def fetch_full_rencontre(item):
        m_id, comp_nom, is_club1, is_club2 = item
        try:
            full_r = client.get_rencontre(m_id)
            return {
                "raw_match": full_r,
                "comp_nom": comp_nom,
                "is_club1": is_club1,
                "is_club2": is_club2,
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        detailed_items = list(executor.map(fetch_full_rencontre, candidate_matches))

    matches_list: list[dict[str, Any]] = []

    for item in detailed_items:
        if not item:
            continue
        m = item["raw_match"]
        comp_nom = item["comp_nom"]
        is_home = item["is_club1"]

        nom_eq1 = getattr(m, "nomEquipe1", "") or ""
        nom_eq2 = getattr(m, "nomEquipe2", "") or ""
        id_org1 = getattr(m, "idOrganismeEquipe1", None)
        id_org2 = getattr(m, "idOrganismeEquipe2", None)
        m_id = str(getattr(m, "id", ""))

        local_team_raw = nom_eq1 if is_home else nom_eq2
        opp_team_raw = nom_eq2 if is_home else nom_eq1
        opp_org_id = id_org2 if is_home else id_org1

        scba_team = normalize_team_name(local_team_raw, comp_nom)
        opponent = clean_opponent_name(opp_team_raw)

        if team and team != "ALL" and team.upper() not in scba_team.upper():
            continue

        # Date & time
        date_raw = str(getattr(m, "date_rencontre", "") or getattr(m, "date", "") or "")
        date_iso = ""
        if re.match(r"^\d{4}-\d{2}-\d{2}", date_raw):
            date_iso = date_raw[:10]

        time_str = "15:00"
        horaire = str(getattr(m, "horaire", "") or "")
        if horaire:
            h_clean = re.sub(r"[hH:]", "", horaire).strip()
            if len(h_clean) == 4:
                time_str = f"{h_clean[:2]}:{h_clean[2:]}"
            elif len(h_clean) == 2:
                time_str = f"{h_clean}:00"
        elif " " in date_raw:
            time_part = date_raw.split(" ")[1][:5]
            if ":" in time_part:
                time_str = time_part

        # Résolution de la salle exacte
        salle_id = getattr(m, "salle", None)
        if is_home:
            if organisme_id == 9326:
                location = "Maison des Sports, Place des Bughes, 63000 Clermont-Ferrand"
            else:
                location = resolve_exact_salle_address(
                    client, salle_id=salle_id, org_id=organisme_id, default_name="Domicile"
                )
        else:
            location = resolve_exact_salle_address(
                client,
                salle_id=salle_id,
                org_id=opp_org_id,
                default_name=f"Extérieur ({opponent})",
            )

        # Opponent Logo
        opponent_logo: Optional[str] = None
        if opp_org_id:
            s_opp_org = str(opp_org_id)
            if s_opp_org in _logo_cache:
                opponent_logo = _logo_cache[s_opp_org]
            else:
                try:
                    opp_org = get_cached_organisme(client, opp_org_id)
                    if opp_org and getattr(opp_org, "logo", None):
                        opp_logo_id = getattr(opp_org.logo, "id", None) or opp_org.logo
                        if opp_logo_id:
                            opponent_logo = f"https://api.ffbb.com/assets/{opp_logo_id}"
                    _logo_cache[s_opp_org] = opponent_logo
                except Exception:
                    _logo_cache[s_opp_org] = None

        match_data: dict[str, Any] = {
            "ffbbMatchId": m_id,
            "team": scba_team,
            "opponent": opponent,
            "date": format_french_date(date_iso),
            "dateISO": date_iso,
            "time": time_str,
            "location": location,
            "isHome": is_home,
            "competition": comp_nom,
            "teamLogo": club_logo_url,
        }
        if opponent_logo:
            match_data["opponentLogo"] = opponent_logo

        matches_list.append(match_data)

    matches_list.sort(key=lambda x: (x.get("dateISO", ""), x.get("time", "")))

    return {
        "organisme_id": organisme_id,
        "club": club_name,
        "matches": matches_list,
        "count": len(matches_list),
    }


@app.get("/api/v1/club/{organisme_id}/teams", tags=["Clubs"])
async def get_club_teams(organisme_id: int):
    """Retourne la liste des équipes engagées pour un organisme/club."""
    client = get_client()
    try:
        org = client.get_organisme(organisme_id)
        if not org:
            raise HTTPException(status_code=404, detail="Club introuvable.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    engagements = getattr(org, "engagements", []) or []
    teams = []
    for eng in engagements:
        comp = getattr(eng, "idCompetition", None)
        poule = getattr(eng, "idPoule", None)
        teams.append({
            "engagement_id": str(getattr(eng, "id", "")),
            "team_number": getattr(eng, "numeroEquipe", "") or "1",
            "competition": getattr(comp, "nom", "") if comp else "",
            "poule_id": str(getattr(poule, "id", "")) if poule else str(poule or ""),
        })

    return {
        "organisme_id": organisme_id,
        "nom": getattr(org, "nom", ""),
        "teams": teams,
        "count": len(teams),
    }


@app.get("/api/v1/club/{organisme_id}", tags=["Clubs"])
async def get_club_details(organisme_id: int):
    """Retourne les informations détaillées d'un club (nom, contacts, adresse, engagements)."""
    client = get_client()
    try:
        org = client.get_organisme(organisme_id)
        if not org:
            raise HTTPException(status_code=404, detail="Club introuvable.")
        return org
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/poule/{poule_id}", tags=["Compétitions"])
async def get_poule(poule_id: int):
    """Retourne les détails, classements et rencontres d'une poule."""
    client = get_client()
    try:
        poule = client.get_poule(poule_id)
        if not poule:
            raise HTTPException(status_code=404, detail="Poule introuvable.")
        return poule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/lives", tags=["Live"])
async def get_lives():
    """Retourne les matchs en direct avec score en temps réel."""
    client = get_client()
    try:
        return client.get_lives()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static documentation website if website/ directory exists
if _WEBSITE_DIR.exists():
    assets_dir = _WEBSITE_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    css_dir = _WEBSITE_DIR / "css"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = _WEBSITE_DIR / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(encoding="utf-8"), status_code=200)
        return {"service": "ffbb-data-client-api", "docs": "/docs"}

    @app.get("/robots.txt", include_in_schema=False)
    async def serve_robots():
        robots_file = _WEBSITE_DIR / "robots.txt"
        if robots_file.exists():
            return FileResponse(robots_file, media_type="text/plain")
        return HTMLResponse("User-agent: *\nAllow: /\n", media_type="text/plain")

    @app.get("/sitemap.xml", include_in_schema=False)
    async def serve_sitemap():
        sitemap_file = _WEBSITE_DIR / "sitemap.xml"
        if sitemap_file.exists():
            return FileResponse(sitemap_file, media_type="application/xml")
        return HTTPException(status_code=404, detail="Sitemap not found")
