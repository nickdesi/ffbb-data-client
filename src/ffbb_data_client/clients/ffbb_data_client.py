from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from typing import Any, cast

import httpx
from httpx import Client

from ..helpers.multi_search_query_helper import generate_queries
from ..models.club_contacts import (
    ClubContacts,
    extract_club_info,
    extract_membres_contacts,
)
from ..models.competitions_multi_search_query import CompetitionsMultiSearchQuery
from ..models.configuration_models import GetConfigurationResponse
from ..models.content_multi_search_query import (
    GaleriesMultiSearchQuery,
    NewsMultiSearchQuery,
    RssMultiSearchQuery,
    YoutubeVideosMultiSearchQuery,
)
from ..models.engagement_contacts import (
    EngagementContacts,
    extract_correspondant,
    extract_entraineur_contact,
)
from ..models.engagements_multi_search_query import EngagementsMultiSearchQuery
from ..models.formations_multi_search_query import FormationsMultiSearchQuery
from ..models.generic_search import (
    GaleriesMultiSearchResult,
    NewsMultiSearchResult,
    RssMultiSearchResult,
    YoutubeVideosMultiSearchResult,
)
from ..models.geo_sort_order import GeoSortOrder
from ..models.get_commune_response import GetCommuneResponse
from ..models.get_competition_response import GetCompetitionResponse
from ..models.get_engagement_response import GetEngagementResponse
from ..models.get_entraineur_response import GetEntraineurResponse
from ..models.get_formation_response import GetFormationResponse
from ..models.get_officiel_response import GetOfficielResponse
from ..models.get_organisme_response import GetOrganismeResponse
from ..models.get_pratique_response import GetPratiqueResponse
from ..models.get_rencontre_response import GetRencontreResponse
from ..models.get_salle_response import GetSalleResponse
from ..models.get_terrain_response import GetTerrainResponse
from ..models.get_tournoi_response import GetTournoiResponse
from ..models.lives import Live
from ..models.multi_search_query import MultiSearchQuery
from ..models.multi_search_result_competitions import CompetitionsMultiSearchResult
from ..models.multi_search_result_engagements import EngagementsMultiSearchResult
from ..models.multi_search_result_formations import FormationsMultiSearchResult
from ..models.multi_search_result_organismes import OrganismesMultiSearchResult
from ..models.multi_search_result_pratiques import PratiquesMultiSearchResult
from ..models.multi_search_result_rencontres import RencontresMultiSearchResult
from ..models.multi_search_result_salles import SallesMultiSearchResult
from ..models.multi_search_result_terrains import TerrainsMultiSearchResult
from ..models.multi_search_result_tournois import TournoisMultiSearchResult
from ..models.multi_search_results import MultiSearchResult
from ..models.multi_search_results_class import MultiSearchResults
from ..models.organismes_multi_search_query import OrganismesMultiSearchQuery
from ..models.poules_models import GetPouleResponse
from ..models.pratiques_multi_search_query import PratiquesMultiSearchQuery
from ..models.rencontres_multi_search_query import RencontresMultiSearchQuery
from ..models.saisons_models import GetSaisonsResponse
from ..models.salles_multi_search_query import SallesMultiSearchQuery
from ..models.team_ranking import TeamRanking
from ..models.terrains_multi_search_query import TerrainsMultiSearchQuery
from ..models.tournois_multi_search_query import TournoisMultiSearchQuery
from ..utils.cache_manager import CacheManager
from ..utils.input_validation import (
    validate_boolean,
    validate_filter_criteria,
    validate_offset,
    validate_search_query,
    validate_string_list,
    validate_token,
)
from ..utils.token_manager import TokenManager
from .api_ffbb_app_client import ApiFFBBAppClient
from .meilisearch_ffbb_client import MeilisearchFFBBClient


class FFBBDataClient:

    def __init__(
        self,
        api_ffbb_client: ApiFFBBAppClient,
        meilisearch_ffbb_client: MeilisearchFFBBClient,
    ):
        self.api_ffbb_client = api_ffbb_client
        self.meilisearch_ffbb_client = meilisearch_ffbb_client
        self.cached_session = api_ffbb_client.cached_session
        self.async_cached_session = api_ffbb_client.async_cached_session

    def get_organisme_for_search(
        self,
        organisme_id: int,
        cached_session: Client | None = None,
    ) -> GetOrganismeResponse | None:
        """Version allégée de get_organisme() pour les contextes de recherche.
        Retourne 31 champs au lieu de 77 (exclut membres, labellisation, salle).
        """
        return self.api_ffbb_client.get_organisme_for_search(
            organisme_id=organisme_id,
            cached_session=cached_session,
        )

    async def get_organisme_for_search_async(
        self,
        organisme_id: int,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetOrganismeResponse | None:
        """Version async allégée de get_organisme() pour les contextes de recherche."""
        return await self.api_ffbb_client.get_organisme_for_search_async(
            organisme_id=organisme_id,
            cached_session=cached_session,
        )

    _BATCH_CHUNK_SIZE = 50

    @staticmethod
    def _chunked(items: list[int], size: int) -> list[list[int]]:
        return [items[i : i + size] for i in range(0, len(items), size)]

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
        # Resolve tokens if not provided
        if meilisearch_bearer_token is None or api_bearer_token is None:
            tokens = TokenManager.get_tokens()
            if meilisearch_bearer_token is None:
                meilisearch_bearer_token = tokens.meilisearch_token
            if api_bearer_token is None:
                api_bearer_token = tokens.api_token

        # Validate inputs with comprehensive checks
        validated_meilisearch_token = validate_token(
            meilisearch_bearer_token, "meilisearch_bearer_token"
        )
        validated_api_token = validate_token(api_bearer_token, "api_bearer_token")
        validated_debug = validate_boolean(debug, "debug")

        # Use singleton session if not provided
        cache_manager = CacheManager()
        if cached_session is None:
            cached_session = cache_manager.session

        if async_cached_session is None:
            async_cached_session = cache_manager.async_session

        # Create API clients with validated parameters
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

    # -------------------------------------------------------------------------
    # REST API — api.ffbb.app
    # -------------------------------------------------------------------------

    def get_configuration(
        self, cached_session: Client | None = None
    ) -> GetConfigurationResponse | None:
        """
        Retrieves the API configuration including bearer tokens.

        Returns:
            GetConfigurationResponse: Configuration data with tokens (key_dh, key_ms)
        """
        return self.api_ffbb_client.get_configuration(cached_session=cached_session)

    async def get_configuration_async(self) -> GetConfigurationResponse | None:
        """Retrieves the API configuration including bearer tokens asynchronously."""
        return await self.api_ffbb_client.get_configuration_async()

    def get_competition(
        self,
        competition_id: int,
        deep_limit: str | None = "1000",
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> GetCompetitionResponse | None:
        """
        Retrieves detailed information about a competition.

        Args:
            competition_id (int): The ID of the competition
            deep_limit (str, optional): Limit for nested rencontres.
                Defaults to "1000".
            fields (List[str], optional): List of fields to retrieve
            cached_session (Client, optional): The cached session to use

        Returns:
            GetCompetitionResponse: Competition data with nested phases,
                poules, and rencontres
        """
        return self.api_ffbb_client.get_competition(
            competition_id=competition_id,
            deep_limit=deep_limit,
            fields=fields,
            cached_session=cached_session,
        )

    def list_competitions(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[GetCompetitionResponse]:
        """
        Lists competitions with optional field selection.

        Args:
            limit (int): Maximum number of competitions to return. Defaults to 10.
            fields (List[str], optional): List of fields to retrieve.
                If None, uses basic fields (id, nom).
            cached_session (Client, optional): The cached session to use

        Returns:
            list[GetCompetitionResponse]: List of competition data
        """
        return self.api_ffbb_client.list_competitions(
            limit=limit,
            fields=fields,
            cached_session=cached_session,
        )

    def get_lives(self, cached_session: Client | None = None) -> list[Live] | None:
        """
        Retrieves a list of live events.

        Args:
            cached_session (Client, optional): The cached session to use

        Returns:
            list[Live]: A list of Live objects representing the live events.
        """
        return self.api_ffbb_client.get_lives(cached_session)

    def get_organisme(
        self,
        organisme_id: int,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> GetOrganismeResponse | None:
        """
        Retrieves detailed information about an organisme.

        Args:
            organisme_id (int): The ID of the organisme
            fields (List[str], optional): List of fields to retrieve
            cached_session (Client, optional): The cached session to use

        Returns:
            GetOrganismeResponse: Organisme data with members, competitions, etc.
        """
        return self.api_ffbb_client.get_organisme(
            organisme_id=organisme_id,
            fields=fields,
            cached_session=cached_session,
        )

    def get_club_contacts(
        self, organisme_id: int, cached_session: Client | None = None
    ) -> ClubContacts | None:
        """Return club contact information (club-level + membres) for an organisme.

        This method delegates to `get_organisme()` and uses the extractor helpers
        to produce a compact `ClubContacts` object.
        """
        organisme = self.get_organisme(organisme_id, cached_session=cached_session)
        if not organisme:
            return None
        club_contact = extract_club_info(organisme)
        membres = extract_membres_contacts(organisme)
        return ClubContacts(
            organisme=organisme, club_contact=club_contact, membres=membres
        )

    def get_poule(
        self,
        poule_id: int,
        deep_limit: str | None = "1000",
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> GetPouleResponse | None:
        """
        Retrieves detailed information about a poule.

        Args:
            poule_id (int): The ID of the poule
            deep_limit (str, optional): Limit for nested rencontres.
                Defaults to "1000".
            fields (List[str], optional): List of fields to retrieve
            cached_session (Client, optional): The cached session to use

        Returns:
            GetPouleResponse: Poule data with rencontres
        """
        return self.api_ffbb_client.get_poule(
            poule_id=poule_id,
            deep_limit=deep_limit,
            fields=fields,
            cached_session=cached_session,
        )

    def get_saisons(
        self,
        fields: list[str] | None = None,
        filter_criteria: str | None = '{"actif":{"_eq":true}}',
        cached_session: Client | None = None,
    ) -> list[GetSaisonsResponse] | None:
        """
        Retrieves list of seasons with comprehensive input validation.

        Args:
            fields (List[str], optional): List of fields to retrieve.
                 Defaults to ["id"].
            filter_criteria (str, optional): JSON filter criteria.
                 Defaults to active seasons.
            cached_session (Client, optional): The cached session to use

        Returns:
            List[GetSaisonsResponse]: List of season data

        Raises:
            ValidationError: If input parameters are invalid
        """
        validated_fields = validate_string_list(fields, "fields")
        validated_filter = validate_filter_criteria(filter_criteria, "filter_criteria")

        return self.api_ffbb_client.get_saisons(
            fields=validated_fields,
            filter_criteria=validated_filter,
            cached_session=cached_session,
        )

    # -------------------------------------------------------------------------
    # REST API — async
    # -------------------------------------------------------------------------

    async def get_lives_async(self) -> list[Live] | None:
        """Retrieves a list of live events asynchronously."""
        return await self.api_ffbb_client.get_lives_async()

    async def get_saisons_async(
        self,
        fields: list[str] | None = None,
        filter_criteria: str | None = '{"actif":{"_eq":true}}',
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetSaisonsResponse]:
        """Retrieves list of seasons asynchronously with input validation."""
        validated_fields = validate_string_list(fields, "fields")
        validated_filter = validate_filter_criteria(filter_criteria, "filter_criteria")
        return await self.api_ffbb_client.get_saisons_async(
            fields=validated_fields,
            filter_criteria=validated_filter,
            cached_session=cached_session,
        )

    async def get_competition_async(
        self,
        competition_id: int,
        deep_limit: str | None = "1000",
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetCompetitionResponse | None:
        """Retrieves detailed information about a competition asynchronously."""
        validated_fields = validate_string_list(fields, "fields")
        return await self.api_ffbb_client.get_competition_async(
            competition_id=competition_id,
            deep_limit=deep_limit,
            fields=validated_fields,
            cached_session=cached_session,
        )

    async def list_competitions_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
    ) -> list[GetCompetitionResponse]:
        """Lists competitions asynchronously."""
        return await self.api_ffbb_client.list_competitions_async(
            limit=limit,
            fields=fields,
        )

    async def get_organisme_async(
        self,
        organisme_id: int,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetOrganismeResponse | None:
        """Retrieves detailed information about an organisme asynchronously."""
        validated_fields = validate_string_list(fields, "fields")
        return await self.api_ffbb_client.get_organisme_async(
            organisme_id=organisme_id,
            fields=validated_fields,
            cached_session=cached_session,
        )

    async def get_poule_async(
        self, poule_id: int, deep_limit: str | None = "1000"
    ) -> GetPouleResponse | None:
        """Retrieves detailed information about a poule asynchronously."""
        return await self.api_ffbb_client.get_poule_async(
            poule_id, deep_limit=deep_limit
        )

    def get_classement(
        self, poule_id: int, cached_session: Client | None = None
    ) -> list[TeamRanking] | None:
        """Retrieves ONLY the ranking (classement) for a specific poule."""
        return self.api_ffbb_client.get_classement(
            poule_id, cached_session=cached_session
        )

    async def get_classement_async(self, poule_id: int) -> list[TeamRanking] | None:
        """Retrieves ONLY the ranking (classement) for a specific poule asynchronously."""
        return await self.api_ffbb_client.get_classement_async(poule_id)

    def get_equipes(
        self, organisme_id: int, cached_session: Client | None = None
    ) -> list[GetOrganismeResponse.EngagementsitemModel] | None:
        """Retrieves ONLY the team commitments (engagements) for a specific club."""
        return self.api_ffbb_client.get_equipes(
            organisme_id, cached_session=cached_session
        )

    async def get_equipes_async(
        self, organisme_id: int
    ) -> list[GetOrganismeResponse.EngagementsitemModel] | None:
        """Retrieves ONLY the team commitments (engagements) for a specific club asynchronously."""
        return await self.api_ffbb_client.get_equipes_async(organisme_id)

    def get_rencontre(
        self, id: str, cached_session: Client | None = None
    ) -> GetRencontreResponse | None:
        """Retrieves detailed information about a rencontre."""
        return self.api_ffbb_client.get_rencontre(id, cached_session=cached_session)

    async def get_rencontre_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetRencontreResponse | None:
        """Asynchronously retrieves detailed information about a rencontre."""
        return await self.api_ffbb_client.get_rencontre_async(
            id, cached_session=cached_session
        )

    def get_engagement(
        self, id: str, cached_session: Client | None = None
    ) -> GetEngagementResponse | None:
        """Retrieves detailed information about an engagement."""
        return self.api_ffbb_client.get_engagement(id, cached_session=cached_session)

    async def get_engagement_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetEngagementResponse | None:
        """Asynchronously retrieves detailed information about an engagement."""
        return await self.api_ffbb_client.get_engagement_async(
            id, cached_session=cached_session
        )

    def get_engagement_contacts(
        self, id: str, cached_session: Client | None = None
    ) -> EngagementContacts | None:
        """Return compact contact information for an engagement.

        The implementation is defensive: it tries several common attribute
        names for entraineur/correspondant fields and returns the best-effort
        `EngagementContacts` object.
        """
        engagement = self.get_engagement(id, cached_session=cached_session)
        if not engagement:
            return None

        correspondant = extract_correspondant(engagement)

        # Try multiple possible attribute names for entraineur id
        entraineur_id = (
            getattr(engagement, "idEntraineur", None)
            or getattr(engagement, "entraineur", None)
            or getattr(engagement, "id_entraineur", None)
        )
        entraineur = (
            self.get_entraineur(str(entraineur_id), cached_session=cached_session)
            if entraineur_id
            else None
        )
        entraineur_contact = extract_entraineur_contact(entraineur, "entraineur")

        entraineur_adjoint_id = (
            getattr(engagement, "idEntraineurAdjoint", None)
            or getattr(engagement, "entraineurAdjoint", None)
            or getattr(engagement, "id_entraineur_adjoint", None)
            or getattr(engagement, "entraineur_adjoint", None)
        )
        entraineur_adjoint = (
            self.get_entraineur(
                str(entraineur_adjoint_id), cached_session=cached_session
            )
            if entraineur_adjoint_id
            else None
        )
        entraineur_adjoint_contact = extract_entraineur_contact(
            entraineur_adjoint, "entraineur_adjoint"
        )

        return EngagementContacts(
            engagement=engagement,
            correspondant=correspondant,
            entraineur=entraineur_contact,
            entraineur_adjoint=entraineur_adjoint_contact,
        )

    async def get_engagement_contacts_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> EngagementContacts | None:
        """Async version: fetch engagement then entraineur & entraineur_adjoint in parallel."""
        engagement = await self.get_engagement_async(id, cached_session=cached_session)
        if not engagement:
            return None

        correspondant = extract_correspondant(engagement)

        entraineur_id = (
            getattr(engagement, "idEntraineur", None)
            or getattr(engagement, "entraineur", None)
            or getattr(engagement, "id_entraineur", None)
        )
        entraineur_adjoint_id = (
            getattr(engagement, "idEntraineurAdjoint", None)
            or getattr(engagement, "entraineurAdjoint", None)
            or getattr(engagement, "id_entraineur_adjoint", None)
            or getattr(engagement, "entraineur_adjoint", None)
        )

        async def _fetch_entraineur(eid: str | None):
            if not eid:
                return None
            return await self.get_entraineur_async(eid, cached_session=cached_session)

        entraineur, entraineur_adjoint = await asyncio.gather(
            _fetch_entraineur(str(entraineur_id) if entraineur_id else None),
            _fetch_entraineur(
                str(entraineur_adjoint_id) if entraineur_adjoint_id else None
            ),
        )

        return EngagementContacts(
            engagement=engagement,
            correspondant=correspondant,
            entraineur=extract_entraineur_contact(entraineur, "entraineur"),
            entraineur_adjoint=extract_entraineur_contact(
                entraineur_adjoint, "entraineur_adjoint"
            ),
        )

    def get_formation(
        self, id: str, cached_session: Client | None = None
    ) -> GetFormationResponse | None:
        """Retrieves detailed information about a formation."""
        return self.api_ffbb_client.get_formation(id, cached_session=cached_session)

    async def get_formation_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetFormationResponse | None:
        """Asynchronously retrieves detailed information about a formation."""
        return await self.api_ffbb_client.get_formation_async(
            id, cached_session=cached_session
        )

    def get_entraineur(
        self, id: str, cached_session: Client | None = None
    ) -> GetEntraineurResponse | None:
        """Retrieves detailed information about an entraineur."""
        return self.api_ffbb_client.get_entraineur(id, cached_session=cached_session)

    async def get_entraineur_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetEntraineurResponse | None:
        """Asynchronously retrieves detailed information about an entraineur."""
        return await self.api_ffbb_client.get_entraineur_async(
            id, cached_session=cached_session
        )

    def get_commune(
        self, id: str, cached_session: Client | None = None
    ) -> GetCommuneResponse | None:
        """Retrieves detailed information about a commune."""
        return self.api_ffbb_client.get_commune(id, cached_session=cached_session)

    async def get_commune_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetCommuneResponse | None:
        """Asynchronously retrieves detailed information about a commune."""
        return await self.api_ffbb_client.get_commune_async(
            id, cached_session=cached_session
        )

    def get_officiel(
        self, id: str, cached_session: Client | None = None
    ) -> GetOfficielResponse | None:
        """Retrieves detailed information about an officiel."""
        return self.api_ffbb_client.get_officiel(id, cached_session=cached_session)

    async def get_officiel_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetOfficielResponse | None:
        """Asynchronously retrieves detailed information about an officiel."""
        return await self.api_ffbb_client.get_officiel_async(
            id, cached_session=cached_session
        )

    def get_salle(
        self, id: str, cached_session: Client | None = None
    ) -> GetSalleResponse | None:
        """Retrieves detailed information about a salle."""
        return self.api_ffbb_client.get_salle(id, cached_session=cached_session)

    async def get_salle_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetSalleResponse | None:
        """Asynchronously retrieves detailed information about a salle."""
        return await self.api_ffbb_client.get_salle_async(
            id, cached_session=cached_session
        )

    def get_terrain(
        self, id: str, cached_session: Client | None = None
    ) -> GetTerrainResponse | None:
        """Retrieves detailed information about a terrain."""
        return self.api_ffbb_client.get_terrain(id, cached_session=cached_session)

    async def get_terrain_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetTerrainResponse | None:
        """Asynchronously retrieves detailed information about a terrain."""
        return await self.api_ffbb_client.get_terrain_async(
            id, cached_session=cached_session
        )

    def get_tournoi(
        self, id: str, cached_session: Client | None = None
    ) -> GetTournoiResponse | None:
        """Retrieves detailed information about a tournoi."""
        return self.api_ffbb_client.get_tournoi(id, cached_session=cached_session)

    async def get_tournoi_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetTournoiResponse | None:
        """Asynchronously retrieves detailed information about a tournoi."""
        return await self.api_ffbb_client.get_tournoi_async(
            id, cached_session=cached_session
        )

    def get_pratique(
        self, id: str, cached_session: Client | None = None
    ) -> GetPratiqueResponse | None:
        """Retrieves detailed information about a pratique."""
        return self.api_ffbb_client.get_pratique(id, cached_session=cached_session)

    async def get_pratique_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetPratiqueResponse | None:
        """Asynchronously retrieves detailed information about a pratique."""
        return await self.api_ffbb_client.get_pratique_async(
            id, cached_session=cached_session
        )

    def get_openapi_spec(self) -> dict[str, Any] | None:
        """Retrieves the current Directus OpenAPI specification."""
        return self.api_ffbb_client.get_openapi_spec()

    def get_session(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves detailed information about a formation session."""
        return self.api_ffbb_client.get_session(id, fields=fields)

    def list_sessions(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists formation sessions."""
        return self.api_ffbb_client.list_sessions(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def get_session_async(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves detailed information about a formation session."""
        return await self.api_ffbb_client.get_session_async(id, fields=fields)

    async def list_sessions_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists formation sessions."""
        return await self.api_ffbb_client.list_sessions_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def get_genius_sport_match(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves detailed Genius Sports match statistics."""
        return self.api_ffbb_client.get_genius_sport_match(id, fields=fields)

    def list_genius_sport_matches(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Genius Sports match statistics."""
        return self.api_ffbb_client.list_genius_sport_matches(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def list_genius_sports_live_logs(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Genius Sports live logs."""
        return self.api_ffbb_client.list_genius_sports_live_logs(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def get_genius_sport_match_async(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves detailed Genius Sports match statistics."""
        return await self.api_ffbb_client.get_genius_sport_match_async(
            id, fields=fields
        )

    async def list_genius_sport_matches_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Genius Sports match statistics."""
        return await self.api_ffbb_client.list_genius_sport_matches_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def get_rematch_video(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves a Rematch video linked to FFBB data."""
        return self.api_ffbb_client.get_rematch_video(id, fields=fields)

    def list_rematch_videos(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Rematch videos linked to FFBB data."""
        return self.api_ffbb_client.list_rematch_videos(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def get_rematch_video_async(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves a Rematch video linked to FFBB data."""
        return await self.api_ffbb_client.get_rematch_video_async(id, fields=fields)

    async def list_rematch_videos_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Rematch videos linked to FFBB data."""
        return await self.api_ffbb_client.list_rematch_videos_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def get_edf_match(
        self, id: str | int, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves an Equipe de France match."""
        return self.api_ffbb_client.get_edf_match(id, fields=fields)

    def list_edf_matches(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France matches."""
        return self.api_ffbb_client.list_edf_matches(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def get_edf_player(
        self, id: str | int, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves an Equipe de France player."""
        return self.api_ffbb_client.get_edf_player(id, fields=fields)

    def list_edf_players(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France players."""
        return self.api_ffbb_client.list_edf_players(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def list_edf_teams(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France teams."""
        return self.api_ffbb_client.list_edf_teams(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def list_edf_rosters(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France rosters."""
        return self.api_ffbb_client.list_edf_rosters(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    # ---------------------------------------------------------------------
    # Directus list delegations (typed)
    # ---------------------------------------------------------------------

    def list_rencontres(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetRencontreResponse]:
        return self.api_ffbb_client.list_rencontres(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    def list_salles(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetSalleResponse]:
        return self.api_ffbb_client.list_salles(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    def list_terrains(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetTerrainResponse]:
        return self.api_ffbb_client.list_terrains(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    def list_tournois(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetTournoiResponse]:
        return self.api_ffbb_client.list_tournois(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    def list_engagements(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetEngagementResponse]:
        return self.api_ffbb_client.list_engagements(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    def list_formations(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetFormationResponse]:
        return self.api_ffbb_client.list_formations(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    def list_entraineurs(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetEntraineurResponse]:
        return self.api_ffbb_client.list_entraineurs(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    def list_communes(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetCommuneResponse]:
        return self.api_ffbb_client.list_communes(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    def list_officiels(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetOfficielResponse]:
        return self.api_ffbb_client.list_officiels(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    def list_pratiques(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetPratiqueResponse]:
        return self.api_ffbb_client.list_pratiques(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_rencontres_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetRencontreResponse]:
        return await self.api_ffbb_client.list_rencontres_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_salles_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetSalleResponse]:
        return await self.api_ffbb_client.list_salles_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_terrains_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetTerrainResponse]:
        return await self.api_ffbb_client.list_terrains_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_tournois_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetTournoiResponse]:
        return await self.api_ffbb_client.list_tournois_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_engagements_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetEngagementResponse]:
        return await self.api_ffbb_client.list_engagements_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_formations_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetFormationResponse]:
        return await self.api_ffbb_client.list_formations_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_entraineurs_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetEntraineurResponse]:
        return await self.api_ffbb_client.list_entraineurs_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_communes_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetCommuneResponse]:
        return await self.api_ffbb_client.list_communes_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_officiels_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetOfficielResponse]:
        return await self.api_ffbb_client.list_officiels_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    async def list_pratiques_async(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetPratiqueResponse]:
        return await self.api_ffbb_client.list_pratiques_async(
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    # ---------------------------------------------------------------------
    # list_all delegations
    # ---------------------------------------------------------------------

    def list_all_rencontres(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetRencontreResponse]:
        return self.api_ffbb_client.list_all_rencontres(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    def list_all_salles(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetSalleResponse]:
        return self.api_ffbb_client.list_all_salles(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    def list_all_terrains(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetTerrainResponse]:
        return self.api_ffbb_client.list_all_terrains(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    def list_all_tournois(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetTournoiResponse]:
        return self.api_ffbb_client.list_all_tournois(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    def list_all_engagements(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetEngagementResponse]:
        return self.api_ffbb_client.list_all_engagements(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    def list_all_formations(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetFormationResponse]:
        return self.api_ffbb_client.list_all_formations(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    def list_all_entraineurs(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetEntraineurResponse]:
        return self.api_ffbb_client.list_all_entraineurs(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    def list_all_communes(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetCommuneResponse]:
        return self.api_ffbb_client.list_all_communes(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    def list_all_officiels(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetOfficielResponse]:
        return self.api_ffbb_client.list_all_officiels(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    def list_all_pratiques(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetPratiqueResponse]:
        return self.api_ffbb_client.list_all_pratiques(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_rencontres_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetRencontreResponse]:
        return await self.api_ffbb_client.list_all_rencontres_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_salles_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetSalleResponse]:
        return await self.api_ffbb_client.list_all_salles_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_terrains_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetTerrainResponse]:
        return await self.api_ffbb_client.list_all_terrains_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_tournois_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetTournoiResponse]:
        return await self.api_ffbb_client.list_all_tournois_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_engagements_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetEngagementResponse]:
        return await self.api_ffbb_client.list_all_engagements_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_formations_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetFormationResponse]:
        return await self.api_ffbb_client.list_all_formations_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_entraineurs_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetEntraineurResponse]:
        return await self.api_ffbb_client.list_all_entraineurs_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_communes_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetCommuneResponse]:
        return await self.api_ffbb_client.list_all_communes_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_officiels_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetOfficielResponse]:
        return await self.api_ffbb_client.list_all_officiels_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    async def list_all_pratiques_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetPratiqueResponse]:
        return await self.api_ffbb_client.list_all_pratiques_async(
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    # ---------------------------------------------------------------------
    # Batch helpers
    # ---------------------------------------------------------------------

    def list_engagements_by_ids(
        self, ids: list[int], cached_session: Client | None = None
    ) -> list[GetEngagementResponse]:
        results: list[GetEngagementResponse] = []
        for chunk in self._chunked(ids, self._BATCH_CHUNK_SIZE):
            fc = json.dumps({"id": {"_in": chunk}})
            results.extend(
                self.list_engagements(
                    limit=len(chunk), filter_criteria=fc, cached_session=cached_session
                )
            )
        return results

    def list_engagements_by_poule(
        self, poule_id: int, cached_session: Client | None = None
    ) -> list[GetEngagementResponse]:
        return self.list_engagements(
            limit=250,
            filter_criteria=json.dumps({"idPoule": {"_eq": poule_id}}),
            cached_session=cached_session,
        )

    def list_engagements_by_poules(
        self, poule_ids: list[int], cached_session: Client | None = None
    ) -> list[GetEngagementResponse]:
        results: list[GetEngagementResponse] = []
        for chunk in self._chunked(poule_ids, self._BATCH_CHUNK_SIZE):
            fc = json.dumps({"idPoule": {"_in": chunk}})
            results.extend(
                self.list_engagements(
                    limit=250, filter_criteria=fc, cached_session=cached_session
                )
            )
        return results

    def list_rencontres_by_poule(
        self, poule_id: int, cached_session: Client | None = None
    ) -> list[GetRencontreResponse]:
        return self.list_rencontres(
            limit=500,
            filter_criteria=json.dumps({"idPoule": {"_eq": poule_id}}),
            cached_session=cached_session,
        )

    def list_rencontres_by_poules(
        self, poule_ids: list[int], cached_session: Client | None = None
    ) -> list[GetRencontreResponse]:
        results: list[GetRencontreResponse] = []
        for chunk in self._chunked(poule_ids, self._BATCH_CHUNK_SIZE):
            fc = json.dumps({"idPoule": {"_in": chunk}})
            results.extend(
                self.list_rencontres(
                    limit=500, filter_criteria=fc, cached_session=cached_session
                )
            )
        return results

    def list_entraineurs_by_ids(
        self, ids: list[int], cached_session: Client | None = None
    ) -> list[GetEntraineurResponse]:
        results: list[GetEntraineurResponse] = []
        for chunk in self._chunked(ids, self._BATCH_CHUNK_SIZE):
            str_ids = [str(i) for i in chunk]
            fc = json.dumps({"idLicence": {"_in": str_ids}})
            results.extend(
                self.list_entraineurs(
                    limit=len(chunk), filter_criteria=fc, cached_session=cached_session
                )
            )
        return results

    # -------------------------------------------------------------------------
    # Meilisearch — multi-search
    # -------------------------------------------------------------------------

    async def multi_search_async(
        self, queries: Sequence[MultiSearchQuery] | None = None
    ) -> MultiSearchResults | None:
        """Performs a smart multi-search asynchronously."""
        return await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )

    def multi_search(
        self, name: str | None = None, cached_session: Client | None = None
    ) -> list[MultiSearchResult] | None:
        """
        Perform multi-search across all resource types with input validation.

        Args:
            name (str, optional): Search query string
            cached_session (Client, optional): HTTP cache session

        Returns:
            list[MultiSearchResult]: Search results across all resource types

        Raises:
            ValidationError: If search query is invalid
        """
        validated_name = validate_search_query(name, "name")
        queries = generate_queries(validated_name)
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session=cached_session
        )

        return results.results if results else None

    # -------------------------------------------------------------------------
    # Meilisearch — competitions
    # -------------------------------------------------------------------------

    def search_competitions(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> CompetitionsMultiSearchResult | None:
        results = self.search_multiple_competitions(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_competitions(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[CompetitionsMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            CompetitionsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )

        return (
            cast(list[CompetitionsMultiSearchResult], results.results)
            if results
            else None
        )

    async def search_competitions_async(
        self, name: str | None = None
    ) -> CompetitionsMultiSearchResult | None:
        """Search for competitions asynchronously."""
        if not name:
            return None
        queries = [CompetitionsMultiSearchQuery(name)]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(CompetitionsMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_competitions_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[CompetitionsMultiSearchResult] | None:
        """Search for multiple competitions asynchronously."""
        if not names:
            return None
        queries = [
            CompetitionsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(list[CompetitionsMultiSearchResult], results.results)
            if results
            else None
        )

    # -------------------------------------------------------------------------
    # Meilisearch — organismes
    # -------------------------------------------------------------------------

    def search_organismes(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> OrganismesMultiSearchResult | None:
        results = self.search_multiple_organismes(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_organismes_by_geo(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        q: str = "",
        limit: int | None = 20,
        geo_sort: GeoSortOrder = GeoSortOrder.NEAREST_FIRST,
        cached_session: Client | None = None,
    ) -> OrganismesMultiSearchResult | None:
        return self.meilisearch_ffbb_client.search_organismes_by_geo(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            q=q,
            limit=limit,
            geo_sort=geo_sort,
            cached_session=cached_session,
        )

    def search_organismes_by_city(
        self,
        city_name: str,
        q: str = "",
        limit: int = 200,
        cached_session: Client | None = None,
    ) -> OrganismesMultiSearchResult | None:
        return self.meilisearch_ffbb_client.search_organismes_by_city(
            city_name, q=q, limit=limit, cached_session=cached_session
        )

    def search_multiple_organismes(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[OrganismesMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            OrganismesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )

        return (
            cast(list[OrganismesMultiSearchResult], results.results)
            if results
            else None
        )

    async def search_organismes_async(
        self, name: str | None = None
    ) -> OrganismesMultiSearchResult | None:
        """Search for organismes asynchronously."""
        if not name:
            return None
        queries = [OrganismesMultiSearchQuery(name)]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(OrganismesMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_organismes_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[OrganismesMultiSearchResult] | None:
        """Search for multiple organismes asynchronously."""
        if not names:
            return None
        queries = [
            OrganismesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(list[OrganismesMultiSearchResult], results.results)
            if results
            else None
        )

    # -------------------------------------------------------------------------
    # Meilisearch — pratiques
    # -------------------------------------------------------------------------

    def search_pratiques(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> PratiquesMultiSearchResult | None:
        results = self.search_multiple_pratiques(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_pratiques(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[PratiquesMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            PratiquesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )

        return (
            cast(list[PratiquesMultiSearchResult], results.results) if results else None
        )

    async def search_pratiques_async(
        self, name: str | None = None
    ) -> PratiquesMultiSearchResult | None:
        """Search for pratiques asynchronously."""
        if not name:
            return None
        queries = [PratiquesMultiSearchQuery(name)]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(PratiquesMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_pratiques_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[PratiquesMultiSearchResult] | None:
        """Search for multiple pratiques asynchronously."""
        if not names:
            return None
        queries = [
            PratiquesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(list[PratiquesMultiSearchResult], results.results) if results else None
        )

    # -------------------------------------------------------------------------
    # Meilisearch — rencontres
    # -------------------------------------------------------------------------

    def search_rencontres(
        self,
        name: str | None = None,
        categorie: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> RencontresMultiSearchResult | None:
        results = self.search_multiple_rencontres(
            [name] if name is not None else None,
            categorie,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_rencontres(
        self,
        names: list[str | None] | None = None,
        categorie: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[RencontresMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            RencontresMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )

        if not results or not results.results:
            return None

        rencontres_results = cast(list[RencontresMultiSearchResult], results.results)

        if categorie:
            for res in rencontres_results:
                if res.hits:
                    filtered_hits = []
                    for hit in res.hits:
                        comp = hit.competition_id
                        cat = comp.categorie if comp else None
                        if (
                            comp
                            and cat
                            and (cat.code == categorie or cat.libelle == categorie)
                        ):
                            filtered_hits.append(hit)
                    res.hits = filtered_hits
                    res.estimated_total_hits = len(filtered_hits)

        return rencontres_results

    async def search_rencontres_async(
        self, name: str | None = None, categorie: str | None = None
    ) -> RencontresMultiSearchResult | None:
        """Search for rencontres asynchronously."""
        if not name:
            return None
        results = await self.search_multiple_rencontres_async([name], categorie)
        return results[0] if results else None

    async def search_multiple_rencontres_async(
        self,
        names: list[str | None] | None = None,
        categorie: str | None = None,
    ) -> list[RencontresMultiSearchResult] | None:
        """Search for multiple rencontres asynchronously."""
        if not names:
            return None

        queries = [RencontresMultiSearchQuery(name) for name in names]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )

        if not results or not results.results:
            return None

        rencontres_results = cast(list[RencontresMultiSearchResult], results.results)

        if categorie:
            for res in rencontres_results:
                if res.hits:
                    # ⚡ Bolt optimization: Use walrus operator to avoid redundant attribute access (~14% speedup)
                    filtered_hits = [
                        hit
                        for hit in res.hits
                        if (comp := hit.competition_id)
                        and (cat := comp.categorie)
                        and (cat.code == categorie or cat.libelle == categorie)
                    ]
                    res.hits = filtered_hits
                    res.estimated_total_hits = len(filtered_hits)

        return rencontres_results

    # -------------------------------------------------------------------------
    # Meilisearch — salles
    # -------------------------------------------------------------------------

    def search_salles(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> SallesMultiSearchResult | None:
        results = self.search_multiple_salles(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_salles_by_geo(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        q: str = "",
        limit: int | None = 20,
        geo_sort: GeoSortOrder = GeoSortOrder.NEAREST_FIRST,
        cached_session: Client | None = None,
    ) -> SallesMultiSearchResult | None:
        return self.meilisearch_ffbb_client.search_salles_by_geo(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            q=q,
            limit=limit,
            geo_sort=geo_sort,
            cached_session=cached_session,
        )

    def search_multiple_salles(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[SallesMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            SallesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )

        return cast(list[SallesMultiSearchResult], results.results) if results else None

    async def search_salles_async(
        self, name: str | None = None
    ) -> SallesMultiSearchResult | None:
        """Search for salles asynchronously."""
        if not name:
            return None
        queries = [SallesMultiSearchQuery(name)]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(SallesMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_salles_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[SallesMultiSearchResult] | None:
        """Search for multiple salles asynchronously."""
        if not names:
            return None
        queries = [
            SallesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return cast(list[SallesMultiSearchResult], results.results) if results else None

    # -------------------------------------------------------------------------
    # Meilisearch — terrains
    # -------------------------------------------------------------------------

    def search_terrains(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> TerrainsMultiSearchResult | None:
        results = self.search_multiple_terrains(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_terrains(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[TerrainsMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            TerrainsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )

        return (
            cast(list[TerrainsMultiSearchResult], results.results) if results else None
        )

    async def search_terrains_async(
        self, name: str | None = None
    ) -> TerrainsMultiSearchResult | None:
        """Search for terrains asynchronously."""
        if not name:
            return None
        queries = [TerrainsMultiSearchQuery(name)]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(TerrainsMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_terrains_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[TerrainsMultiSearchResult] | None:
        """Search for multiple terrains asynchronously."""
        if not names:
            return None
        queries = [
            TerrainsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(list[TerrainsMultiSearchResult], results.results) if results else None
        )

    # -------------------------------------------------------------------------
    # Meilisearch — tournois
    # -------------------------------------------------------------------------

    def search_tournois(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> TournoisMultiSearchResult | None:
        results = self.search_multiple_tournois(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_tournois(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[TournoisMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            TournoisMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )

        return (
            cast(list[TournoisMultiSearchResult], results.results) if results else None
        )

    async def search_tournois_async(
        self, name: str | None = None
    ) -> TournoisMultiSearchResult | None:
        """Search for tournois asynchronously."""
        if not name:
            return None
        queries = [TournoisMultiSearchQuery(name)]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(TournoisMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_tournois_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[TournoisMultiSearchResult] | None:
        """Search for multiple tournois asynchronously."""
        if not names:
            return None
        queries = [
            TournoisMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(list[TournoisMultiSearchResult], results.results) if results else None
        )

    # -------------------------------------------------------------------------
    # Meilisearch — engagements
    # -------------------------------------------------------------------------

    def search_engagements(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> EngagementsMultiSearchResult | None:
        results = self.search_multiple_engagements(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_engagements_by_geo(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        q: str = "",
        limit: int | None = 20,
        geo_sort: GeoSortOrder = GeoSortOrder.NEAREST_FIRST,
        cached_session: Client | None = None,
    ) -> EngagementsMultiSearchResult | None:
        return self.meilisearch_ffbb_client.search_engagements_by_geo(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            q=q,
            limit=limit,
            geo_sort=geo_sort,
            cached_session=cached_session,
        )

    def search_engagements_filtered(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        q: str = "",
        limit: int | None = 5000,
        sexes: list[str] | None = None,
        niveau_codes: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> EngagementsMultiSearchResult | None:
        return self.meilisearch_ffbb_client.search_engagements_filtered(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            q=q,
            limit=limit,
            sexes=sexes,
            niveau_codes=niveau_codes,
            cached_session=cached_session,
        )

    def search_multiple_engagements(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[EngagementsMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            EngagementsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )

        return (
            cast(list[EngagementsMultiSearchResult], results.results)
            if results
            else None
        )

    async def search_engagements_async(
        self, name: str | None = None
    ) -> EngagementsMultiSearchResult | None:
        """Search for engagements asynchronously."""
        if not name:
            return None
        queries = [EngagementsMultiSearchQuery(name)]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(EngagementsMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_engagements_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[EngagementsMultiSearchResult] | None:
        """Search for multiple engagements asynchronously."""
        if not names:
            return None
        queries = [
            EngagementsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(list[EngagementsMultiSearchResult], results.results)
            if results
            else None
        )

    # -------------------------------------------------------------------------
    # Meilisearch — formations
    # -------------------------------------------------------------------------

    def search_formations(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> FormationsMultiSearchResult | None:
        results = self.search_multiple_formations(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_formations(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[FormationsMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            FormationsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )

        return (
            cast(list[FormationsMultiSearchResult], results.results)
            if results
            else None
        )

    async def search_formations_async(
        self, name: str | None = None
    ) -> FormationsMultiSearchResult | None:
        """Search for formations asynchronously."""
        if not name:
            return None
        queries = [FormationsMultiSearchQuery(name)]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(FormationsMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_formations_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[FormationsMultiSearchResult] | None:
        """Search for multiple formations asynchronously."""
        if not names:
            return None
        queries = [
            FormationsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self.meilisearch_ffbb_client.recursive_smart_multi_search_async(
            queries
        )
        return (
            cast(list[FormationsMultiSearchResult], results.results)
            if results
            else None
        )

    # -------------------------------------------------------------------------
    # Meilisearch — content indexes
    # -------------------------------------------------------------------------

    def search_news(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> NewsMultiSearchResult | None:
        results = self.search_multiple_news(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_news(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[NewsMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            NewsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )
        return cast(list[NewsMultiSearchResult], results.results) if results else None

    def search_youtube_videos(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> YoutubeVideosMultiSearchResult | None:
        results = self.search_multiple_youtube_videos(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_youtube_videos(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[YoutubeVideosMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            YoutubeVideosMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[YoutubeVideosMultiSearchResult], results.results)
            if results
            else None
        )

    def search_rss(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> RssMultiSearchResult | None:
        results = self.search_multiple_rss(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_rss(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[RssMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            RssMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )
        return cast(list[RssMultiSearchResult], results.results) if results else None

    def search_galeries(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> GaleriesMultiSearchResult | None:
        results = self.search_multiple_galeries(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_galeries(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[GaleriesMultiSearchResult] | None:
        if not names:
            return None

        queries = [
            GaleriesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self.meilisearch_ffbb_client.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[GaleriesMultiSearchResult], results.results) if results else None
        )
