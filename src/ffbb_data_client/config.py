"""Centralized configuration for FFBB API client."""

import os

# API URLs
API_FFBB_BASE_URL = "https://api.ffbb.app/"
MEILISEARCH_BASE_URL = "https://meilisearch-prod.ffbb.app/"

# HTTP Headers
# BunnyCDN WAF on Directus (api.ffbb.app) blocks "okhttp/*" over IPv4 with HTTP 403 Forbidden.
# Use an authentic iOS Safari User-Agent by default, overridable via FFBB_USER_AGENT.
DEFAULT_USER_AGENT = os.getenv(
    "FFBB_USER_AGENT",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
)

# User-Agents de secours pour contournement transparent et auto-healing en cas de durcissement WAF BunnyCDN
FALLBACK_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

# Environment variable names for tokens
ENV_API_TOKEN = "API_FFBB_APP_BEARER_TOKEN"  # noqa: S105
ENV_MEILISEARCH_TOKEN = "MEILISEARCH_BEARER_TOKEN"  # noqa: S105

# API Endpoint Paths (relative to base URL)
ENDPOINT_CONFIGURATION = "items/configuration"
ENDPOINT_LIVES = "json/lives.json"
ENDPOINT_COMPETITIONS = "items/ffbbserver_competitions"
ENDPOINT_POULES = "items/ffbbserver_poules"
ENDPOINT_SAISONS = "items/ffbbserver_saisons"
ENDPOINT_ORGANISMES = "items/ffbbserver_organismes"
ENDPOINT_RENCONTRES = "items/ffbbserver_rencontres"
ENDPOINT_ENGAGEMENTS = "items/ffbbserver_engagements"
ENDPOINT_FORMATIONS = "items/ffbbserver_formations"
ENDPOINT_ENTRAINEURS = "items/ffbbserver_entraineurs"
ENDPOINT_COMMUNES = "items/ffbbserver_communes"
ENDPOINT_OFFICIELS = "items/ffbbserver_officiels"
ENDPOINT_SALLES = "items/ffbbserver_salles"
ENDPOINT_TERRAINS = "items/ffbbserver_terrains"
ENDPOINT_TOURNOIS = "items/ffbbserver_tournois"
ENDPOINT_PRATIQUES = "items/ffbbnational_pratiques"
ENDPOINT_SESSIONS = "items/ffbbserver_sessions"
ENDPOINT_GENIUS_SPORT_MATCHES = "items/genius_sport_matches"
ENDPOINT_GENIUS_SPORTS_LIVE_LOGS = "items/genius_sports_live_logs"
ENDPOINT_REMATCH_VIDEOS = "items/rematch_videos"
ENDPOINT_EDF_ARENAS = "items/edf_arenas"
ENDPOINT_EDF_CAMPAIGNS = "items/edf_campaigns"
ENDPOINT_EDF_CITIES = "items/edf_cities"
ENDPOINT_EDF_COACHES = "items/edf_coaches"
ENDPOINT_EDF_COMPETITION_TYPES = "items/edf_competition_types"
ENDPOINT_EDF_COUNTRIES = "items/edf_countries"
ENDPOINT_EDF_MATCHES = "items/edf_matches"
ENDPOINT_EDF_OPPONENTS = "items/edf_opponents"
ENDPOINT_EDF_PLAYERS = "items/edf_players"
ENDPOINT_EDF_POSITIONS = "items/edf_positions"
ENDPOINT_EDF_ROSTERS = "items/edf_rosters"
ENDPOINT_EDF_SELECTION = "items/edf_selection"
ENDPOINT_EDF_STAFFS = "items/edf_staffs"
ENDPOINT_EDF_TEAMS = "items/edf_teams"
ENDPOINT_ASSETS = "assets/"
ENDPOINT_OPENAPI = "server/specs/oas"

# Meilisearch Endpoint Paths
MEILISEARCH_ENDPOINT_MULTI_SEARCH = "multi-search"

# Meilisearch Index UIDs
MEILISEARCH_INDEX_ORGANISMES = "ffbbserver_organismes"
MEILISEARCH_INDEX_RENCONTRES = "ffbbserver_rencontres"
MEILISEARCH_INDEX_TERRAINS = "ffbbserver_terrains"
MEILISEARCH_INDEX_SALLES = "ffbbserver_salles"
MEILISEARCH_INDEX_TOURNOIS = "ffbbserver_tournois"
MEILISEARCH_INDEX_COMPETITIONS = "ffbbserver_competitions"
MEILISEARCH_INDEX_ENGAGEMENTS = "ffbbserver_engagements"
MEILISEARCH_INDEX_FORMATIONS = "ffbbserver_formations"
MEILISEARCH_INDEX_PRATIQUES = "ffbbnational_pratiques"
MEILISEARCH_INDEX_NEWS = "ffbbsite_news"
MEILISEARCH_INDEX_YOUTUBE_VIDEOS = "youtube_videos"
MEILISEARCH_INDEX_RSS = "ffbbnational_rss"
MEILISEARCH_INDEX_GALERIES = "ffbbnational_galeries"

MEILISEARCH_INDEX_UIDS = [
    MEILISEARCH_INDEX_ORGANISMES,
    MEILISEARCH_INDEX_RENCONTRES,
    MEILISEARCH_INDEX_TERRAINS,
    MEILISEARCH_INDEX_SALLES,
    MEILISEARCH_INDEX_TOURNOIS,
    MEILISEARCH_INDEX_COMPETITIONS,
    MEILISEARCH_INDEX_ENGAGEMENTS,
    MEILISEARCH_INDEX_FORMATIONS,
    MEILISEARCH_INDEX_PRATIQUES,
    MEILISEARCH_INDEX_NEWS,
    MEILISEARCH_INDEX_YOUTUBE_VIDEOS,
    MEILISEARCH_INDEX_RSS,
    MEILISEARCH_INDEX_GALERIES,
]

# Meilisearch Default Facets per Index
MEILISEARCH_FACETS_ORGANISMES = [
    "type_association.libelle",
    "type",
    "labellisation",
    "offresPratiques",
]
MEILISEARCH_FACETS_RENCONTRES = [
    "competitionId.categorie.code",
    "competitionId.typeCompetition",
    "niveau",
    "competitionId.sexe",
    "organisateur.nom",
    "organisateur.id",
    "competitionId.nomExtended",
]
MEILISEARCH_FACETS_TOURNOIS = [
    "sexe",
    "tournoiTypes3x3.libelle",
    "tournoiType",
]
MEILISEARCH_FACETS_PRATIQUES = [
    "label",
    "type",
]
MEILISEARCH_FACETS_ENGAGEMENTS = [
    "clubPro",
    "idCompetition.categorie.code",
    "idCompetition.categorie.libelle",
    "idCompetition.code",
    "idCompetition.nom",
    "idCompetition.sexe",
    "idPoule.nom",
    "niveau.code",
    "niveau.libelle",
]
MEILISEARCH_FACETS_FORMATIONS = [
    "date_end_formatted",
    "date_start_formatted",
    "domain",
    "mode",
    "place",
    "places",
    "postal_code",
    "postal_codes",
    "theme",
    "type",
]
MEILISEARCH_FACETS_NEWS = [
    "category",
    "categories",
    "type",
]
MEILISEARCH_FACETS_YOUTUBE_VIDEOS = [
    "tags",
    "type",
]
MEILISEARCH_FACETS_RSS = [
    "categories",
    "tags",
]
MEILISEARCH_FACETS_GALERIES = [
    "tags",
    "type",
]
