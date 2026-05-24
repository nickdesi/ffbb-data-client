from __future__ import annotations

import httpx
from httpx import Client

from ..utils.cache_manager import CacheManager
from ..utils.input_validation import validate_boolean, validate_token
from ..utils.token_manager import TokenManager
from ._rest_facade import _RestFacade
from ._search_facade import _SearchFacade
from .api_ffbb_app_client import ApiFFBBAppClient
from .meilisearch_ffbb_client import MeilisearchFFBBClient

_REST_METHODS = [
    "get_organisme_for_search",
    "get_organisme_for_search_async",
    "get_configuration",
    "get_configuration_async",
    "get_competition",
    "get_competition_async",
    "list_competitions",
    "list_competitions_async",
    "get_lives",
    "get_lives_async",
    "get_organisme",
    "get_organisme_async",
    "get_club_contacts",
    "get_poule",
    "get_poule_async",
    "get_saisons",
    "get_saisons_async",
    "get_classement",
    "get_classement_async",
    "get_equipes",
    "get_equipes_async",
    "get_rencontre",
    "get_rencontre_async",
    "get_engagement",
    "get_engagement_async",
    "get_engagement_contacts",
    "get_formation",
    "get_formation_async",
    "get_entraineur",
    "get_entraineur_async",
    "get_commune",
    "get_commune_async",
    "get_officiel",
    "get_officiel_async",
    "get_salle",
    "get_salle_async",
    "get_terrain",
    "get_terrain_async",
    "get_tournoi",
    "get_tournoi_async",
    "get_pratique",
    "get_pratique_async",
    "get_openapi_spec",
    "get_openapi_spec_async",
    "get_session",
    "get_session_async",
    "list_sessions",
    "list_sessions_async",
    "get_genius_sport_match",
    "get_genius_sport_match_async",
    "list_genius_sport_matches",
    "list_genius_sport_matches_async",
    "list_genius_sports_live_logs",
    "list_genius_sports_live_logs_async",
    "get_rematch_video",
    "get_rematch_video_async",
    "list_rematch_videos",
    "list_rematch_videos_async",
    "get_edf_match",
    "get_edf_match_async",
    "list_edf_matches",
    "list_edf_matches_async",
    "get_edf_player",
    "get_edf_player_async",
    "list_edf_players",
    "list_edf_players_async",
    "list_edf_teams",
    "list_edf_teams_async",
    "list_edf_rosters",
    "list_edf_rosters_async",
    "list_rencontres",
    "list_rencontres_async",
    "list_salles",
    "list_salles_async",
    "list_terrains",
    "list_terrains_async",
    "list_tournois",
    "list_tournois_async",
    "list_engagements",
    "list_engagements_async",
    "list_formations",
    "list_formations_async",
    "list_entraineurs",
    "list_entraineurs_async",
    "list_communes",
    "list_communes_async",
    "list_officiels",
    "list_officiels_async",
    "list_pratiques",
    "list_pratiques_async",
    "list_all_rencontres",
    "list_all_rencontres_async",
    "list_all_salles",
    "list_all_salles_async",
    "list_all_terrains",
    "list_all_terrains_async",
    "list_all_tournois",
    "list_all_tournois_async",
    "list_all_engagements",
    "list_all_engagements_async",
    "list_all_formations",
    "list_all_formations_async",
    "list_all_entraineurs",
    "list_all_entraineurs_async",
    "list_all_communes",
    "list_all_communes_async",
    "list_all_officiels",
    "list_all_officiels_async",
    "list_all_pratiques",
    "list_all_pratiques_async",
    "list_engagements_by_ids",
    "list_engagements_by_poule",
    "list_engagements_by_poules",
    "list_rencontres_by_poule",
    "list_rencontres_by_poules",
    "list_entraineurs_by_ids",
]

_SEARCH_METHODS = [
    "multi_search",
    "multi_search_async",
    "search_competitions",
    "search_multiple_competitions",
    "search_competitions_async",
    "search_multiple_competitions_async",
    "search_organismes",
    "search_organismes_by_geo",
    "search_organismes_by_city",
    "search_multiple_organismes",
    "search_organismes_async",
    "search_multiple_organismes_async",
    "search_pratiques",
    "search_multiple_pratiques",
    "search_pratiques_async",
    "search_multiple_pratiques_async",
    "search_rencontres",
    "search_multiple_rencontres",
    "search_rencontres_async",
    "search_multiple_rencontres_async",
    "search_salles",
    "search_salles_by_geo",
    "search_multiple_salles",
    "search_salles_async",
    "search_multiple_salles_async",
    "search_terrains",
    "search_multiple_terrains",
    "search_terrains_async",
    "search_multiple_terrains_async",
    "search_tournois",
    "search_multiple_tournois",
    "search_tournois_async",
    "search_multiple_tournois_async",
    "search_engagements",
    "search_engagements_by_geo",
    "search_engagements_filtered",
    "search_multiple_engagements",
    "search_engagements_async",
    "search_multiple_engagements_async",
    "search_formations",
    "search_multiple_formations",
    "search_formations_async",
    "search_multiple_formations_async",
    "search_news",
    "search_multiple_news",
    "search_youtube_videos",
    "search_multiple_youtube_videos",
    "search_rss",
    "search_multiple_rss",
    "search_galeries",
    "search_multiple_galeries",
]


class FFBBDataClient(_RestFacade, _SearchFacade):
    """Facade that provides unified sync and async access to FFBB data."""

    def __init__(
        self,
        api_ffbb_client: ApiFFBBAppClient,
        meilisearch_ffbb_client: MeilisearchFFBBClient,
    ):
        self.api_ffbb_client = api_ffbb_client
        self.meilisearch_ffbb_client = meilisearch_ffbb_client
        self.cached_session = api_ffbb_client.cached_session
        self.async_cached_session = api_ffbb_client.async_cached_session

        _RestFacade.__init__(self, api_ffbb_client, meilisearch_ffbb_client)
        _SearchFacade.__init__(self, api_ffbb_client, meilisearch_ffbb_client)

        self._rest = self
        self._search = self

    @staticmethod
    def create(
        meilisearch_bearer_token: str | None = None,
        api_bearer_token: str | None = None,
        debug: bool = False,
        cached_session: Client | None = None,
        async_cached_session: httpx.AsyncClient | None = None,
    ) -> FFBBDataClient:
        """
        Create a new FFBB Data Client instance with comprehensive input validation.

        Args:
            meilisearch_bearer_token (str, optional): Bearer token for Meilisearch API.
                If None, resolved via TokenManager.
            api_bearer_token (str, optional): Bearer token for FFBB API.
                If None, resolved via TokenManager.
            debug (bool, optional): Enable debug logging. Defaults to False.
            cached_session (Client, optional): HTTP cache session
            async_cached_session (AsyncClient, optional): Async HTTP cache session

        Returns:
            FFBBDataClient: Configured API client instance

        Raises:
            ValidationError: If any input parameter is invalid
        """
        if meilisearch_bearer_token is None or api_bearer_token is None:
            tokens = TokenManager.get_tokens()
            if meilisearch_bearer_token is None:
                meilisearch_bearer_token = tokens.meilisearch_token
            if api_bearer_token is None:
                api_bearer_token = tokens.api_token

        validated_meilisearch_token = validate_token(
            meilisearch_bearer_token, "meilisearch_bearer_token"
        )
        validated_api_token = validate_token(api_bearer_token, "api_bearer_token")
        validated_debug = validate_boolean(debug, "debug")

        cache_manager = CacheManager()
        if cached_session is None:
            cached_session = cache_manager.session
        if async_cached_session is None:
            async_cached_session = cache_manager.async_session

        api_ffbb_client = ApiFFBBAppClient(
            validated_api_token,
            debug=validated_debug,
            cached_session=cached_session,
            async_cached_session=async_cached_session,
        )

        meilisearch_ffbb_client: MeilisearchFFBBClient = MeilisearchFFBBClient(
            validated_meilisearch_token,
            debug=validated_debug,
            cached_session=cached_session,
            async_cached_session=async_cached_session,
        )

        return FFBBDataClient(api_ffbb_client, meilisearch_ffbb_client)
