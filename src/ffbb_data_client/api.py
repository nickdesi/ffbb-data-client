"""
FastAPI REST API for FFBB Data Client.
Provides public HTTP endpoints, Scalar modern documentation at /docs,
Swagger UI at /swagger, ReDoc at /redoc, and hosts the official website at /.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections import OrderedDict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi import Path as PathParam
from fastapi import Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .clients.ffbb_data_client import FFBBDataClient
from .models.query_fields_manager import QueryFieldsManager
from .utils.retry_utils import aclose_default_clients

# Directories
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_WEBSITE_DIR = _BASE_DIR / "website"
if not _WEBSITE_DIR.exists():
    _WEBSITE_DIR = Path("/app/website")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and graceful shutdown (FastAPI/Context7 standard)."""
    yield
    await aclose_default_clients()


TAGS_METADATA = [
    {
        "name": "Clubs",
        "description": "Fiches détaillées, contacts, gymnases et liste des équipes engagées des 4 500+ clubs affiliés FFBB.",
    },
    {
        "name": "Matchs & Calendriers",
        "description": "Calendriers officiels, programmation des rencontres, dates, horaires et résolution des gymnases.",
    },
    {
        "name": "Compétitions & Poules",
        "description": "Compositions de poules, classements officiels détaillés (points, victoires, défaites, goal-average) et résultats.",
    },
    {
        "name": "Scores en Direct",
        "description": "Scores live en temps réel, statut et évolution des matchs en direct le week-end sur toutes les divisions.",
    },
    {
        "name": "Recherche & Meilisearch",
        "description": "Moteur de recherche rapide multi-index : clubs, compétitions, tournois 3x3, gymnases et arbitres.",
    },
    {
        "name": "Monitoring & Diagnostic",
        "description": "Health check, diagnostic des connexions Directus/Meilisearch et état de fonctionnement du service.",
    },
]

app = FastAPI(
    title="FFBB REST API — Données Officielles du Basket Français",
    description="""
# 🏀 API REST FFBB & Open Data Basketball

Bienvenue sur la documentation interactive officielle de l'API **FFBB Data Client**.

Cette API REST moderne et asynchrone (FastAPI + Pydantic v2) permet d'interroger directement
l'ensemble des données publiques de la **Fédération Française de BasketBall** :
- **Clubs & Équipes** : fiches, contacts, adresses et engagements (du niveau départemental à la Betclic Élite).
- **Compétitions & Poules** : calendriers, résultats, feuilles de match et classements officiels.
- **Scores Live** : suivi en temps réel des matchs le week-end.
- **Moteur de recherche** : recherche universelle multi-index optimisée par Meilisearch.

---

### 📚 Écosystème & Liens Utiles
- 📦 **SDK Python (PyPI)** : [`pip install ffbb-data-client`](https://pypi.org/project/ffbb-data-client/)
- 🤖 **Serveur MCP pour assistants IA** : [`https://ffbb.desimone.fr`](https://ffbb.desimone.fr)
- ⭐ **Code Source GitHub** : [`https://github.com/nickdesi/ffbb-data-client`](https://github.com/nickdesi/ffbb-data-client)
- 📖 **Documentation Sphinx complète** : [`https://nickdesi.github.io/ffbb-data-client/`](https://nickdesi.github.io/ffbb-data-client/)
""",
    version="2.3.4",
    openapi_tags=TAGS_METADATA,
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
    servers=[
        {
            "url": "https://ffbb-api.desimone.fr",
            "description": "Serveur de Production (Live API)",
        },
        {
            "url": "http://localhost:8000",
            "description": "Serveur Local de Développement",
        },
    ],
    lifespan=lifespan,
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
_client: FFBBDataClient | None = None


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


class LRUCache:
    """Bounded LRU cache with TTL eviction using collections.OrderedDict."""

    def __init__(self, maxsize: int = 1024, default_ttl: float | None = 3600.0):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: OrderedDict[Any, tuple[Any, float | None]] = OrderedDict()

    def get(self, key: Any, default: Any = None) -> Any:
        if key not in self._cache:
            return default
        val, expiry = self._cache[key]
        if expiry is not None and time.monotonic() > expiry:
            del self._cache[key]
            return default
        self._cache.move_to_end(key)
        return val

    def set(self, key: Any, value: Any, ttl: float | None = None) -> None:
        effective_ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.monotonic() + effective_ttl if effective_ttl is not None else None
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, expiry)
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

    def __contains__(self, key: Any) -> bool:
        if key not in self._cache:
            return False
        val, expiry = self._cache[key]
        if expiry is not None and time.monotonic() > expiry:
            del self._cache[key]
            return False
        return True

    def __getitem__(self, key: Any) -> Any:
        val = self.get(key)
        if val is None and key not in self:
            raise KeyError(key)
        return val

    def __setitem__(self, key: Any, value: Any) -> None:
        self.set(key, value)


# Cache dictionaries with bounded capacity
_org_cache = LRUCache(maxsize=1024)
_logo_cache = LRUCache(maxsize=2048)
_salle_cache = LRUCache(maxsize=2048)


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
        if org:
            _org_cache[oid] = org
        return org
    except Exception:
        return None


async def get_cached_organisme_async(client, org_id: Any):
    if not org_id:
        return None
    try:
        oid = int(org_id)
    except Exception:
        return None
    if oid in _org_cache:
        return _org_cache[oid]
    try:
        org = await client.get_organisme_async(oid)
        if org:
            _org_cache[oid] = org
        return org
    except Exception:
        return None


def resolve_exact_salle_address(
    client, salle_id: Any = None, org_id: Any = None, default_name: str = ""
) -> str:
    """Résout l'adresse complète et exacte du gymnase via l'API FFBB (Nom, Rue, CP Ville) de façon synchrone."""
    s_id_clean = (
        str(getattr(salle_id, "id", None) or salle_id or "").strip() if salle_id else ""
    )
    org_id_clean = str(org_id or "").strip() if org_id else ""

    # Mutualisation de cache : recherche par salle directe, par organisme, ou par clé composite
    if s_id_clean and f"salle_{s_id_clean}" in _salle_cache:
        return str(_salle_cache[f"salle_{s_id_clean}"])
    if not s_id_clean and org_id_clean and f"org_{org_id_clean}" in _salle_cache:
        return str(_salle_cache[f"org_{org_id_clean}"])
    cache_key = f"{s_id_clean}_{org_id_clean}"
    if cache_key in _salle_cache:
        return str(_salle_cache[cache_key])

    nom = ""
    adresse = ""
    cp = ""
    ville = ""

    if salle_id:
        try:
            s_id = getattr(salle_id, "id", None) or salle_id
            salle = client.get_salle(str(s_id))
            if salle:
                nom = getattr(salle, "libelle", "") or getattr(salle, "nom", "") or ""
                adresse = getattr(salle, "adresse", "") or ""
                cp = getattr(salle, "codePostal", "") or getattr(salle, "cp", "") or ""
                ville = getattr(salle, "ville", "") or ""
        except Exception:
            pass

    if salle_id and (not cp or not ville):
        try:
            s_id_str = str(getattr(salle_id, "id", None) or salle_id)
            queries = [adresse] if adresse else []
            if nom:
                queries.append(nom)
            for q in queries:
                res = client.search_salles(q)
                if res and getattr(res, "hits", None):
                    for h in res.hits:
                        carto_id = getattr(
                            getattr(h, "cartographie", None), "cartographie_id", ""
                        )
                        if (
                            carto_id == f"S-{s_id_str}"
                            or str(getattr(h, "id", "")) == s_id_str
                        ):
                            c = getattr(h, "commune", None)
                            if c:
                                cp = (
                                    getattr(c, "code_postal", "")
                                    or getattr(c, "codePostal", "")
                                    or ""
                                )
                                ville = getattr(c, "libelle", "") or ""
                            break
                if cp and ville:
                    break
        except Exception:
            pass

    if org_id and (not cp or not ville or not nom or not adresse):
        try:
            org = get_cached_organisme(client, org_id)
            if org:
                o_salle = getattr(org, "salle", None)
                if o_salle:
                    if not nom:
                        nom = (
                            getattr(o_salle, "libelle", "")
                            or getattr(o_salle, "nom", "")
                            or ""
                        )
                    if not adresse:
                        adresse = getattr(o_salle, "adresse", "") or ""
                    c = getattr(o_salle, "commune", None)
                    if c:
                        if not cp:
                            cp = (
                                getattr(c, "codePostal", "")
                                or getattr(c, "code_postal", "")
                                or ""
                            )
                        if not ville:
                            ville = getattr(c, "libelle", "") or ""

                if not cp or not ville:
                    c = getattr(org, "commune", None)
                    if c:
                        if not cp:
                            cp = (
                                getattr(c, "codePostal", "")
                                or getattr(c, "code_postal", "")
                                or ""
                            )
                        if not ville:
                            ville = getattr(c, "libelle", "") or ""
        except Exception:
            pass

    cp_ville = f"{cp} {ville}".strip()
    parts = [p for p in [nom, adresse, cp_ville] if p]
    if parts:
        res = ", ".join(parts)
        _salle_cache[cache_key] = res
        if s_id_clean:
            _salle_cache[f"salle_{s_id_clean}"] = res
        if org_id_clean and not s_id_clean:
            _salle_cache[f"org_{org_id_clean}"] = res
        return res

    return default_name or "Lieu à confirmer"


async def resolve_exact_salle_address_async(
    client, salle_id: Any = None, org_id: Any = None, default_name: str = ""
) -> str:
    """Résout l'adresse complète et exacte du gymnase de façon asynchrone non-bloquante."""
    s_id_clean = (
        str(getattr(salle_id, "id", None) or salle_id or "").strip() if salle_id else ""
    )
    org_id_clean = str(org_id or "").strip() if org_id else ""

    # Mutualisation de cache : recherche par salle directe, par organisme, ou par clé composite
    if s_id_clean and f"salle_{s_id_clean}" in _salle_cache:
        return str(_salle_cache[f"salle_{s_id_clean}"])
    if not s_id_clean and org_id_clean and f"org_{org_id_clean}" in _salle_cache:
        return str(_salle_cache[f"org_{org_id_clean}"])
    cache_key = f"{s_id_clean}_{org_id_clean}"
    if cache_key in _salle_cache:
        return str(_salle_cache[cache_key])

    nom = ""
    adresse = ""
    cp = ""
    ville = ""

    if salle_id:
        try:
            s_id = getattr(salle_id, "id", None) or salle_id
            salle = await client.get_salle_async(str(s_id))
            if salle:
                nom = getattr(salle, "libelle", "") or getattr(salle, "nom", "") or ""
                adresse = getattr(salle, "adresse", "") or ""
                cp = getattr(salle, "codePostal", "") or getattr(salle, "cp", "") or ""
                ville = getattr(salle, "ville", "") or ""
        except Exception:
            pass

    if salle_id and (not cp or not ville):
        try:
            s_id_str = str(getattr(salle_id, "id", None) or salle_id)
            queries = [adresse] if adresse else []
            if nom:
                queries.append(nom)
            for q in queries:
                res = await client.search_salles_async(q)
                if res and getattr(res, "hits", None):
                    for h in res.hits:
                        carto_id = getattr(
                            getattr(h, "cartographie", None), "cartographie_id", ""
                        )
                        if (
                            carto_id == f"S-{s_id_str}"
                            or str(getattr(h, "id", "")) == s_id_str
                        ):
                            c = getattr(h, "commune", None)
                            if c:
                                cp = (
                                    getattr(c, "code_postal", "")
                                    or getattr(c, "codePostal", "")
                                    or ""
                                )
                                ville = getattr(c, "libelle", "") or ""
                            break
                if cp and ville:
                    break
        except Exception:
            pass

    if org_id and (not cp or not ville or not nom or not adresse):
        try:
            org = await get_cached_organisme_async(client, org_id)
            if org:
                o_salle = getattr(org, "salle", None)
                if o_salle:
                    if not nom:
                        nom = (
                            getattr(o_salle, "libelle", "")
                            or getattr(o_salle, "nom", "")
                            or ""
                        )
                    if not adresse:
                        adresse = getattr(o_salle, "adresse", "") or ""
                    c = getattr(o_salle, "commune", None)
                    if c:
                        if not cp:
                            cp = (
                                getattr(c, "codePostal", "")
                                or getattr(c, "code_postal", "")
                                or ""
                            )
                        if not ville:
                            ville = getattr(c, "libelle", "") or ""

                if not cp or not ville:
                    c = getattr(org, "commune", None)
                    if c:
                        if not cp:
                            cp = (
                                getattr(c, "codePostal", "")
                                or getattr(c, "code_postal", "")
                                or ""
                            )
                        if not ville:
                            ville = getattr(c, "libelle", "") or ""
        except Exception:
            pass

    cp_ville = f"{cp} {ville}".strip()
    parts = [p for p in [nom, adresse, cp_ville] if p]
    if parts:
        res = ", ".join(parts)
        _salle_cache[cache_key] = res
        if s_id_clean:
            _salle_cache[f"salle_{s_id_clean}"] = res
        if org_id_clean and not s_id_clean:
            _salle_cache[f"org_{org_id_clean}"] = res
        return res

    return default_name or "Lieu à confirmer"


@app.get(
    "/health", tags=["Monitoring & Diagnostic"], summary="Diagnostic de l'API (/health)"
)
async def health():
    """Vérifie l'état de fonctionnement et la disponibilité de l'API REST."""
    return {
        "status": "healthy",
        "service": "ffbb-data-client-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.head("/health", include_in_schema=False)
async def health_head():
    return Response(status_code=200)


@app.get(
    "/api/v1/search",
    tags=["Recherche & Meilisearch"],
    summary="Recherche universelle (Clubs, Compétitions, Salles)",
    response_description="Résultats multi-index Meilisearch groupés par typologie",
)
async def search_ffbb(
    query: str = Query(
        ...,
        title="Terme de recherche",
        description="Nom d'un club, d'une compétition, ville, salle ou tournoi",
        min_length=2,
        examples=["Stade Clermontois"],
    ),
    q: str | None = Query(
        None,
        include_in_schema=False,
        description="Alias court optionnel pour compatibilité ?q=",
    ),
):
    """
    Recherche universelle rapide multi-index optimisée par Meilisearch.

    Permet d'interroger simultanément :
    - 🏀 **Clubs & Organismes** (nom officiel, sigle, commune, code postal)
    - 🏆 **Compétitions & Championnats** (départemental, régional, national)
    - 📍 **Salles & Gymnases** (nom, adresse, ville)
    - ⚡ **Tournois & Terrains 3x3**
    """
    search_term = (query or q or "").strip()
    if len(search_term) < 2:
        raise HTTPException(
            status_code=400,
            detail="Le terme de recherche doit comporter au moins 2 caractères.",
        )
    client = get_client()
    try:
        results = client.multi_search(name=search_term)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de recherche: {e}")


@app.get(
    "/api/v1/club/{organisme_id}/matches",
    tags=["Matchs & Calendriers"],
    summary="Calendrier & Matchs d'un club",
    response_description="Liste ordonnée des rencontres avec adresses et logos",
)
async def get_club_matches(
    organisme_id: int = PathParam(
        ...,
        ge=1,
        description="ID Organisme FFBB (ex: 9326 pour SCBA)",
        examples=[9326],
    ),
    team: str | None = Query(
        None,
        description="Filtrer par équipe (ex: 'SENIOR M1', 'U18 M1', 'ALL')",
        examples=["SENIOR M1"],
    ),
):
    """
    Récupère l'ensemble des rencontres officielles FFBB d'un club,
    avec détection domicile/extérieur, calcul des équipes, salles résolues avec adresse exacte et logos officiels.
    """
    client = get_client()

    try:
        org = await client.get_organisme_async(organisme_id)
        if not org:
            raise HTTPException(
                status_code=404, detail=f"Club {organisme_id} introuvable."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur FFBB: {e}")

    club_name = getattr(org, "nom", "") or "Club"
    club_logo_url: str | None = None
    if getattr(org, "logo", None):
        logo_id = getattr(org.logo, "id", None) or org.logo
        if logo_id:
            club_logo_url = f"https://api.ffbb.com/assets/{logo_id}"

    engagements = getattr(org, "engagements", []) or []
    _poule_name_cache: dict[str, str] = {}

    # 1. Déduplication et préparation des requêtes de poules
    poule_meta: dict[int, dict[str, Any]] = {}
    for eng in engagements:
        poule_obj = getattr(eng, "idPoule", None)
        comp_obj = getattr(eng, "idCompetition", None)
        poule_id_raw = getattr(poule_obj, "id", None) or (
            str(poule_obj) if poule_obj else None
        )
        if not poule_id_raw:
            continue
        try:
            pid = int(poule_id_raw)
        except Exception:
            continue

        comp_nom = getattr(comp_obj, "nom", "") or ""
        comp_id = getattr(comp_obj, "id", None) or getattr(
            comp_obj, "competition_origine", None
        )
        if pid not in poule_meta:
            poule_meta[pid] = {
                "comp_nom": comp_nom,
                "comp_id": int(comp_id) if comp_id else None,
            }

    # 2. Récupération asynchrone concurrente de l'ensemble des poules
    sem_poule = asyncio.Semaphore(10)

    async def fetch_poule(pid: int):
        async with sem_poule:
            try:
                p = await client.get_poule_async(pid)
                return pid, p
            except Exception:
                return pid, None

    poule_results = await asyncio.gather(*(fetch_poule(pid) for pid in poule_meta))
    poules_by_id = dict(poule_results)

    # 3. Résolution des noms de poules manquants via get_competition_async
    missing_comp_tasks = []
    for pid, p in poules_by_id.items():
        if p:
            p_nom = getattr(p, "nom", None)
            cid = poule_meta[pid]["comp_id"]
            if not p_nom and cid:
                missing_comp_tasks.append((pid, cid))

    if missing_comp_tasks:

        async def fetch_comp_poule_name(pid: int, cid: int):
            try:
                comp_data = await client.get_competition_async(cid)
                if comp_data and getattr(comp_data, "poules", None):
                    for cp in comp_data.poules:
                        if str(getattr(cp, "id", "")) == str(pid):
                            return pid, getattr(cp, "nom", "") or ""
            except Exception:
                pass
            return pid, ""

        comp_results = await asyncio.gather(
            *(fetch_comp_poule_name(p, c) for p, c in missing_comp_tasks)
        )
        for pid, resolved_nom in comp_results:
            if resolved_nom:
                _poule_name_cache[str(pid)] = resolved_nom

    # 4. Identification des rencontres candidates pour le club
    candidate_matches = []
    seen_match_ids: set[str] = set()

    for pid, poule in poules_by_id.items():
        if not poule:
            continue
        rencontres = getattr(poule, "rencontres", []) or []
        comp_nom = poule_meta[pid]["comp_nom"]
        poule_nom = getattr(poule, "nom", None) or _poule_name_cache.get(str(pid), "")

        for m in rencontres:
            m_id = str(getattr(m, "id", "") or "")
            if not m_id or m_id in seen_match_ids:
                continue

            nom_eq1 = getattr(m, "nomEquipe1", "") or ""
            nom_eq2 = getattr(m, "nomEquipe2", "") or ""
            id_org1 = str(getattr(m, "idOrganismeEquipe1", "") or "")
            id_org2 = str(getattr(m, "idOrganismeEquipe2", "") or "")

            is_club1 = (
                id_org1 == str(organisme_id) or club_name.upper() in nom_eq1.upper()
            )
            is_club2 = (
                id_org2 == str(organisme_id) or club_name.upper() in nom_eq2.upper()
            )

            if not is_club1 and not is_club2:
                continue

            seen_match_ids.add(m_id)
            candidate_matches.append(
                (m_id, comp_nom, str(pid), poule_nom or "", is_club1, is_club2)
            )

    # 5. Récupération asynchrone non-bloquante des fiches rencontres détaillées
    sem_rencontre = asyncio.Semaphore(10)

    async def fetch_full_rencontre_async(item):
        m_id, comp_nom, poule_id, poule_nom, is_club1, is_club2 = item
        async with sem_rencontre:
            try:
                full_r = await client.get_rencontre_async(m_id)
                return {
                    "raw_match": full_r,
                    "comp_nom": comp_nom,
                    "poule_id": poule_id,
                    "poule_nom": poule_nom,
                    "is_club1": is_club1,
                    "is_club2": is_club2,
                }
            except Exception:
                return None

    detailed_items = await asyncio.gather(
        *(fetch_full_rencontre_async(c) for c in candidate_matches)
    )

    # 6. Construction et enrichissement des cartes de matchs
    async def build_match_card(item):
        if not item:
            return None
        m = item["raw_match"]
        if not m:
            return None
        comp_nom = item["comp_nom"]
        poule_id = item.get("poule_id", "")
        poule_nom = item.get("poule_nom", "")
        is_home = item["is_club1"]

        nom_eq1 = getattr(m, "nomEquipe1", "") or ""
        nom_eq2 = getattr(m, "nomEquipe2", "") or ""
        id_org1_raw = getattr(m, "idOrganismeEquipe1", None)
        id_org2_raw = getattr(m, "idOrganismeEquipe2", None)
        m_id = str(getattr(m, "id", ""))

        local_team_raw = nom_eq1 if is_home else nom_eq2
        opp_team_raw = nom_eq2 if is_home else nom_eq1
        opp_org_id = id_org2_raw if is_home else id_org1_raw

        scba_team = normalize_team_name(local_team_raw, comp_nom)
        opponent = clean_opponent_name(opp_team_raw)

        if team and team != "ALL" and team.upper() not in scba_team.upper():
            return None

        # Date & time
        date_raw = str(getattr(m, "date_rencontre", "") or getattr(m, "date", "") or "")
        date_iso = ""
        if re.match(r"^\d{4}-\d{2}-\d{2}", date_raw):
            date_iso = date_raw[:10]

        time_str = ""
        horaire = str(getattr(m, "horaire", "") or "").strip()
        if horaire and horaire not in ("0", "00:00", "00h00"):
            h_clean = re.sub(r"[hH:]", "", horaire).strip()
            if len(h_clean) == 4:
                time_str = f"{h_clean[:2]}:{h_clean[2:]}"
            elif len(h_clean) == 2:
                time_str = f"{h_clean}:00"
        elif " " in date_raw:
            time_part = date_raw.split(" ")[1][:5]
            if ":" in time_part and time_part not in ("00:00", "00:00:00"):
                time_str = time_part

        # Résolution de la salle exacte de façon asynchrone
        salle_id = getattr(m, "salle", None)
        if is_home:
            fallback_name = (
                "Maison des Sports, Place des Bughes, 63000 Clermont-Ferrand"
                if organisme_id == 9326
                else "Domicile"
            )
            location = await resolve_exact_salle_address_async(
                client,
                salle_id=salle_id,
                org_id=organisme_id,
                default_name=fallback_name,
            )
        else:
            location = await resolve_exact_salle_address_async(
                client,
                salle_id=salle_id,
                org_id=opp_org_id,
                default_name=f"Extérieur ({opponent})",
            )

        # Opponent Logo
        opponent_logo: str | None = None
        if opp_org_id:
            s_opp_org = str(opp_org_id)
            if s_opp_org in _logo_cache:
                opponent_logo = _logo_cache[s_opp_org]
            else:
                try:
                    opp_org = await get_cached_organisme_async(client, opp_org_id)
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
            "poule": poule_nom,
            "pouleId": poule_id,
            "teamLogo": club_logo_url,
        }
        if opponent_logo:
            match_data["opponentLogo"] = opponent_logo

        return match_data

    built_matches = await asyncio.gather(
        *(build_match_card(item) for item in detailed_items if item)
    )
    matches_list = [m for m in built_matches if m is not None]

    matches_list.sort(key=lambda x: (x.get("dateISO", ""), x.get("time", "")))

    return {
        "organisme_id": organisme_id,
        "club": club_name,
        "matches": matches_list,
        "count": len(matches_list),
    }


@app.get(
    "/api/v1/club/{organisme_id}/teams",
    tags=["Clubs"],
    summary="Équipes engagées d'un club",
    response_description="Liste des équipes engagées par championnat",
)
async def get_club_teams(
    organisme_id: int = PathParam(
        ...,
        ge=1,
        description="ID Organisme FFBB (ex: 9326)",
        examples=[9326],
    ),
):
    """Retourne la liste des équipes engagées pour un organisme/club."""
    client = get_client()
    try:
        org = await client.get_organisme_async(organisme_id)
        if not org:
            raise HTTPException(status_code=404, detail="Club introuvable.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    engagements = getattr(org, "engagements", []) or []
    teams = []
    for eng in engagements:
        comp = getattr(eng, "idCompetition", None)
        poule = getattr(eng, "idPoule", None)
        teams.append(
            {
                "engagement_id": str(getattr(eng, "id", "")),
                "team_number": getattr(eng, "numeroEquipe", "") or "1",
                "competition": getattr(comp, "nom", "") if comp else "",
                "poule_id": (
                    str(getattr(poule, "id", "")) if poule else str(poule or "")
                ),
            }
        )

    return {
        "organisme_id": organisme_id,
        "nom": getattr(org, "nom", ""),
        "teams": teams,
        "count": len(teams),
    }


@app.get(
    "/api/v1/club/{organisme_id}",
    tags=["Clubs"],
    summary="Fiche détaillée d'un club",
    response_description="Informations administratives, contacts et salle",
)
async def get_club_details(
    organisme_id: int = PathParam(
        ...,
        ge=1,
        description="ID Organisme FFBB (ex: 9326)",
        examples=[9326],
    ),
):
    """Retourne les informations détaillées d'un club (nom, contacts, adresse, engagements)."""
    client = get_client()
    try:
        org = await client.get_organisme_async(organisme_id)
        if not org:
            raise HTTPException(status_code=404, detail="Club introuvable.")
        return org
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/poule/{poule_id}",
    tags=["Compétitions & Poules"],
    summary="Détails complets d'une poule",
    response_description="Composition, classements et rencontres",
)
async def get_poule(
    poule_id: int = PathParam(
        ..., ge=1, description="ID de la poule FFBB", examples=[129759]
    ),
):
    """Retourne les détails complets, classements et rencontres d'une poule."""
    client = get_client()
    try:
        poule = await client.get_poule_async(poule_id)
        if not poule:
            raise HTTPException(status_code=404, detail="Poule introuvable.")
        return poule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/poule/{poule_id}/classement",
    tags=["Compétitions & Poules"],
    summary="Classement officiel d'une poule",
    response_description="Classement détaillé avec points, victoires et goal-average",
)
async def get_poule_classement(
    poule_id: int = PathParam(
        ..., ge=1, description="ID de la poule FFBB", examples=[129759]
    ),
):
    """Retourne le classement officiel d'une poule avec victoires, défaites, points et goal-average."""
    client = get_client()
    try:
        poule = await client.get_poule_async(
            poule_id,
            fields=QueryFieldsManager.get_classement_fields(),
        )
        if not poule:
            raise HTTPException(status_code=404, detail="Poule introuvable.")
        classement = (
            getattr(poule, "classement", None)
            or getattr(poule, "classements", [])
            or []
        )
        return {
            "poule_id": poule_id,
            "nom": getattr(poule, "nom", "") or getattr(poule, "libelle", ""),
            "classement": classement,
            "count": len(classement),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/lives",
    tags=["Scores en Direct"],
    summary="Scores en direct du week-end (Lives)",
    response_description="Matchs en direct avec scores temps réel",
)
async def get_lives():
    """Retourne les matchs en direct avec score en temps réel sur l'ensemble des championnats."""
    client = get_client()
    try:
        return await client.get_lives_async()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------------------
# Modern API Documentation Interfaces (Scalar, Swagger UI, ReDoc)
# --------------------------------------------------------------------------


@app.api_route("/docs", methods=["GET", "HEAD"], include_in_schema=False)
async def scalar_api_reference(request: Request):
    """Modern interactive API Reference powered by Scalar."""
    if request.method == "HEAD":
        return Response(status_code=200, media_type="text/html")
    html_content = """<!doctype html>
<html lang="fr">
  <head>
    <title>API FFBB — Documentation & Interactive API Reference</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" type="image/png" sizes="48x48" href="/assets/favicon-48x48.png">
    <style>
      body { margin: 0; padding: 0; background: #07090e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    </style>
  </head>
  <body>
    <script
      id="api-reference"
      data-url="/openapi.json"
      data-configuration='{
        "theme": "purple",
        "darkMode": true,
        "showSidebar": true,
        "searchHotKey": "k",
        "defaultHttpClient": {
          "targetKey": "python",
          "clientKey": "httpx"
        }
      }'></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>
"""
    return HTMLResponse(content=html_content, status_code=200)


@app.api_route("/swagger", methods=["GET", "HEAD"], include_in_schema=False)
async def swagger_ui(request: Request):
    """Standard Clean Swagger UI without broken CSS overrides."""
    if request.method == "HEAD":
        return Response(status_code=200, media_type="text/html")
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="API FFBB — Swagger UI",
        swagger_favicon_url="/assets/favicon-48x48.png",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": 1,
            "docExpansion": "list",
            "filter": True,
            "displayRequestDuration": True,
            "tryItOutEnabled": True,
        },
    )


@app.api_route("/redoc", methods=["GET", "HEAD"], include_in_schema=False)
async def redoc_ui(request: Request):
    """ReDoc Documentation."""
    if request.method == "HEAD":
        return Response(status_code=200, media_type="text/html")
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="API FFBB — ReDoc",
        redoc_favicon_url="/assets/favicon-48x48.png",
    )


# --------------------------------------------------------------------------
# Serve static documentation website if website/ directory exists
# --------------------------------------------------------------------------

if _WEBSITE_DIR.exists():
    assets_dir = _WEBSITE_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    css_dir = _WEBSITE_DIR / "css"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")

    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_index(request: Request):
        index_file = _WEBSITE_DIR / "index.html"
        if index_file.exists():
            if request.method == "HEAD":
                return Response(status_code=200, media_type="text/html")
            return HTMLResponse(
                content=index_file.read_text(encoding="utf-8"), status_code=200
            )
        return {
            "service": "ffbb-data-client-api",
            "docs": "/docs",
            "swagger": "/swagger",
            "redoc": "/redoc",
        }

    @app.api_route("/robots.txt", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_robots(request: Request):
        if request.method == "HEAD":
            return Response(status_code=200, media_type="text/plain")
        robots_file = _WEBSITE_DIR / "robots.txt"
        if robots_file.exists():
            return FileResponse(robots_file, media_type="text/plain")
        return HTMLResponse("User-agent: *\nAllow: /\n", media_type="text/plain")

    @app.api_route("/sitemap.xml", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_sitemap(request: Request):
        if request.method == "HEAD":
            return Response(status_code=200, media_type="application/xml")
        sitemap_file = _WEBSITE_DIR / "sitemap.xml"
        if sitemap_file.exists():
            return FileResponse(sitemap_file, media_type="application/xml")
        return HTTPException(status_code=404, detail="Sitemap not found")

    @app.api_route("/llms.txt", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_llms(request: Request):
        if request.method == "HEAD":
            return Response(status_code=200, media_type="text/plain")
        llms_file = _WEBSITE_DIR / "llms.txt"
        if llms_file.exists():
            return FileResponse(llms_file, media_type="text/plain")
        return HTTPException(status_code=404, detail="llms.txt not found")

    @app.api_route("/llms-full.txt", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_llms_full(request: Request):
        if request.method == "HEAD":
            return Response(status_code=200, media_type="text/plain")
        llms_full_file = _WEBSITE_DIR / "llms-full.txt"
        if llms_full_file.exists():
            return FileResponse(llms_full_file, media_type="text/plain")
        return HTTPException(status_code=404, detail="llms-full.txt not found")

else:

    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    async def fallback_index(request: Request):
        if request.method == "HEAD":
            return Response(status_code=200, media_type="application/json")
        return {
            "service": "ffbb-data-client-api",
            "docs": "/docs",
            "swagger": "/swagger",
            "redoc": "/redoc",
        }
