from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
from httpx import Client

from ..models.club_contacts import (
    ClubContacts,
    extract_club_info,
    extract_membres_contacts,
)
from ..models.configuration_models import GetConfigurationResponse
from ..models.engagement_contacts import (
    EngagementContacts,
    extract_correspondant,
    extract_entraineur_contact,
)
from ..models.get_commune_response import GetCommuneResponse
from ..models.get_competition_response import GetCompetitionResponse
from ..models.get_engagement_response import GetEngagementResponse
from ..models.get_entraineur_response import GetEntraineurResponse
from ..models.get_formation_response import GetFormationResponse
from ..models.get_officiel_response import GetOfficielResponse
from ..models.get_organisme_response import GetOrganismeResponse
from ..models.get_poule_response import GetPouleResponse
from ..models.get_pratique_response import GetPratiqueResponse
from ..models.get_rencontre_response import GetRencontreResponse
from ..models.get_saisons_response import GetSaisonsResponse
from ..models.get_salle_response import GetSalleResponse
from ..models.get_terrain_response import GetTerrainResponse
from ..models.get_tournoi_response import GetTournoiResponse
from ..models.lives import Live
from ..models.team_ranking import TeamRanking
from ..utils.input_validation import (
    validate_filter_criteria,
    validate_offset,
    validate_search_query,
    validate_string_list,
)
from .api_ffbb_app_client import ApiFFBBAppClient
from .meilisearch_ffbb_client import MeilisearchFFBBClient


class _RestFacade:
    """Facade delegating all REST API (Directus api.ffbb.app) calls to ApiFFBBAppClient."""

    _BATCH_CHUNK_SIZE = 50

    def __init__(
        self,
        api_ffbb_client: ApiFFBBAppClient,
        meilisearch_ffbb_client: MeilisearchFFBBClient,
    ):
        self._api = api_ffbb_client
        self._meilisearch = meilisearch_ffbb_client

    @staticmethod
    def _chunked(items: list[int], size: int) -> list[list[int]]:
        return [items[i : i + size] for i in range(0, len(items), size)]

    # ------------------------------------------------------------------
    # organisme for search
    # ------------------------------------------------------------------

    def get_organisme_for_search(
        self,
        organisme_id: int,
        cached_session: Client | None = None,
    ) -> GetOrganismeResponse | None:
        """Version allégée de get_organisme() pour les contextes de recherche.
        Retourne 31 champs au lieu de 77 (exclut membres, labellisation, salle).
        """
        return self._api.get_organisme_for_search(
            organisme_id=organisme_id,
            cached_session=cached_session,
        )

    async def get_organisme_for_search_async(
        self,
        organisme_id: int,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetOrganismeResponse | None:
        """Version async allégée de get_organisme() pour les contextes de recherche."""
        return await self._api.get_organisme_for_search_async(
            organisme_id=organisme_id,
            cached_session=cached_session,
        )

    # ------------------------------------------------------------------
    # REST API — api.ffbb.app (sync)
    # ------------------------------------------------------------------

    def get_configuration(
        self, cached_session: Client | None = None
    ) -> GetConfigurationResponse | None:
        """
        Retrieves the API configuration including bearer tokens.

        Returns:
            GetConfigurationResponse: Configuration data with tokens (key_dh, key_ms)
        """
        return self._api.get_configuration(cached_session=cached_session)

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
        return self._api.get_competition(
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
        return self._api.list_competitions(
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
        return self._api.get_lives(cached_session)

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
        return self._api.get_organisme(
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
        return self._api.get_poule(
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
        return self._api.get_saisons(
            fields=validated_fields,
            filter_criteria=validated_filter,
            cached_session=cached_session,
        )

    def get_classement(
        self, poule_id: int, cached_session: Client | None = None
    ) -> list[TeamRanking] | None:
        """Retrieves ONLY the ranking (classement) for a specific poule."""
        return self._api.get_classement(poule_id, cached_session=cached_session)

    def get_equipes(
        self, organisme_id: int, cached_session: Client | None = None
    ) -> list[GetOrganismeResponse.EngagementsitemModel] | None:
        """Retrieves ONLY the team commitments (engagements) for a specific club."""
        return self._api.get_equipes(organisme_id, cached_session=cached_session)

    def get_rencontre(
        self, id: str, cached_session: Client | None = None
    ) -> GetRencontreResponse | None:
        """Retrieves detailed information about a rencontre."""
        return self._api.get_rencontre(id, cached_session=cached_session)

    def get_engagement(
        self, id: str, cached_session: Client | None = None
    ) -> GetEngagementResponse | None:
        """Retrieves detailed information about an engagement."""
        return self._api.get_engagement(id, cached_session=cached_session)

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
        """Async version: return compact contact information for an engagement.

        Fetches entraineur and entraineur_adjoint in parallel for ~33% speedup.
        """
        engagement = await self._api.get_engagement_async(
            id, cached_session=cached_session
        )
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

        import asyncio

        entraineur_task = (
            self._api.get_entraineur_async(
                str(entraineur_id), cached_session=cached_session
            )
            if entraineur_id
            else asyncio.sleep(0, result=None)
        )
        entraineur_adjoint_task = (
            self._api.get_entraineur_async(
                str(entraineur_adjoint_id), cached_session=cached_session
            )
            if entraineur_adjoint_id
            else asyncio.sleep(0, result=None)
        )
        entraineur, entraineur_adjoint = await asyncio.gather(
            entraineur_task, entraineur_adjoint_task
        )

        entraineur_contact = extract_entraineur_contact(entraineur, "entraineur")
        entraineur_adjoint_contact = extract_entraineur_contact(
            entraineur_adjoint, "entraineur_adjoint"
        )

        return EngagementContacts(
            engagement=engagement,
            correspondant=correspondant,
            entraineur=entraineur_contact,
            entraineur_adjoint=entraineur_adjoint_contact,
        )

    def get_formation(
        self, id: str, cached_session: Client | None = None
    ) -> GetFormationResponse | None:
        """Retrieves detailed information about a formation."""
        return self._api.get_formation(id, cached_session=cached_session)

    def get_entraineur(
        self, id: str, cached_session: Client | None = None
    ) -> GetEntraineurResponse | None:
        """Retrieves detailed information about an entraineur."""
        return self._api.get_entraineur(id, cached_session=cached_session)

    def get_commune(
        self, id: str, cached_session: Client | None = None
    ) -> GetCommuneResponse | None:
        """Retrieves detailed information about a commune."""
        return self._api.get_commune(id, cached_session=cached_session)

    def get_officiel(
        self, id: str, cached_session: Client | None = None
    ) -> GetOfficielResponse | None:
        """Retrieves detailed information about an officiel."""
        return self._api.get_officiel(id, cached_session=cached_session)

    def get_salle(
        self, id: str, cached_session: Client | None = None
    ) -> GetSalleResponse | None:
        """Retrieves detailed information about a salle."""
        return self._api.get_salle(id, cached_session=cached_session)

    def get_terrain(
        self, id: str, cached_session: Client | None = None
    ) -> GetTerrainResponse | None:
        """Retrieves detailed information about a terrain."""
        return self._api.get_terrain(id, cached_session=cached_session)

    def get_tournoi(
        self, id: str, cached_session: Client | None = None
    ) -> GetTournoiResponse | None:
        """Retrieves detailed information about a tournoi."""
        return self._api.get_tournoi(id, cached_session=cached_session)

    def get_pratique(
        self, id: str, cached_session: Client | None = None
    ) -> GetPratiqueResponse | None:
        """Retrieves detailed information about a pratique."""
        return self._api.get_pratique(id, cached_session=cached_session)

    def get_openapi_spec(self) -> dict[str, Any] | None:
        """Retrieves the current Directus OpenAPI specification."""
        return self._api.get_openapi_spec()

    def get_session(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves detailed information about a formation session."""
        return self._api.get_session(id, fields=fields)

    def list_sessions(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists formation sessions."""
        return self._api.list_sessions(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def get_genius_sport_match(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves detailed Genius Sports match statistics."""
        return self._api.get_genius_sport_match(id, fields=fields)

    def list_genius_sport_matches(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Genius Sports match statistics."""
        return self._api.list_genius_sport_matches(
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
        return self._api.list_genius_sports_live_logs(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def get_rematch_video(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves a Rematch video linked to FFBB data."""
        return self._api.get_rematch_video(id, fields=fields)

    def list_rematch_videos(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Rematch videos linked to FFBB data."""
        return self._api.list_rematch_videos(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def get_edf_match(
        self, id: str | int, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves an Equipe de France match."""
        return self._api.get_edf_match(id, fields=fields)

    def list_edf_matches(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France matches."""
        return self._api.list_edf_matches(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    def get_edf_player(
        self, id: str | int, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Retrieves an Equipe de France player."""
        return self._api.get_edf_player(id, fields=fields)

    def list_edf_players(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France players."""
        return self._api.list_edf_players(
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
        return self._api.list_edf_teams(
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
        return self._api.list_edf_rosters(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    # ------------------------------------------------------------------
    # REST API — async
    # ------------------------------------------------------------------

    async def get_lives_async(self) -> list[Live] | None:
        """Retrieves a list of live events asynchronously."""
        return await self._api.get_lives_async()

    async def get_configuration_async(self) -> GetConfigurationResponse | None:
        """Retrieves the API configuration including bearer tokens asynchronously."""
        return await self._api.get_configuration_async()

    async def get_saisons_async(
        self,
        fields: list[str] | None = None,
        filter_criteria: str | None = '{"actif":{"_eq":true}}',
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetSaisonsResponse]:
        """Retrieves list of seasons asynchronously with input validation."""
        validated_fields = validate_string_list(fields, "fields")
        validated_filter = validate_filter_criteria(filter_criteria, "filter_criteria")
        return await self._api.get_saisons_async(
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
        return await self._api.get_competition_async(
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
        return await self._api.list_competitions_async(
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
        return await self._api.get_organisme_async(
            organisme_id=organisme_id,
            fields=validated_fields,
            cached_session=cached_session,
        )

    async def get_poule_async(
        self, poule_id: int, deep_limit: str | None = "1000"
    ) -> GetPouleResponse | None:
        """Retrieves detailed information about a poule asynchronously."""
        return await self._api.get_poule_async(poule_id, deep_limit=deep_limit)

    async def get_classement_async(self, poule_id: int) -> list[TeamRanking] | None:
        """Retrieves ONLY the ranking (classement) for a specific poule asynchronously."""
        return await self._api.get_classement_async(poule_id)

    async def get_equipes_async(
        self, organisme_id: int
    ) -> list[GetOrganismeResponse.EngagementsitemModel] | None:
        """Retrieves ONLY the team commitments (engagements) for a specific club asynchronously."""
        return await self._api.get_equipes_async(organisme_id)

    async def get_rencontre_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetRencontreResponse | None:
        """Asynchronously retrieves detailed information about a rencontre."""
        return await self._api.get_rencontre_async(id, cached_session=cached_session)

    async def get_engagement_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetEngagementResponse | None:
        """Asynchronously retrieves detailed information about an engagement."""
        return await self._api.get_engagement_async(id, cached_session=cached_session)

    async def get_formation_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetFormationResponse | None:
        """Asynchronously retrieves detailed information about a formation."""
        return await self._api.get_formation_async(id, cached_session=cached_session)

    async def get_entraineur_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetEntraineurResponse | None:
        """Asynchronously retrieves detailed information about an entraineur."""
        return await self._api.get_entraineur_async(id, cached_session=cached_session)

    async def get_commune_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetCommuneResponse | None:
        """Asynchronously retrieves detailed information about a commune."""
        return await self._api.get_commune_async(id, cached_session=cached_session)

    async def get_officiel_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetOfficielResponse | None:
        """Asynchronously retrieves detailed information about an officiel."""
        return await self._api.get_officiel_async(id, cached_session=cached_session)

    async def get_salle_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetSalleResponse | None:
        """Asynchronously retrieves detailed information about a salle."""
        return await self._api.get_salle_async(id, cached_session=cached_session)

    async def get_terrain_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetTerrainResponse | None:
        """Asynchronously retrieves detailed information about a terrain."""
        return await self._api.get_terrain_async(id, cached_session=cached_session)

    async def get_tournoi_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetTournoiResponse | None:
        """Asynchronously retrieves detailed information about a tournoi."""
        return await self._api.get_tournoi_async(id, cached_session=cached_session)

    async def get_pratique_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetPratiqueResponse | None:
        """Asynchronously retrieves detailed information about a pratique."""
        return await self._api.get_pratique_async(id, cached_session=cached_session)

    async def get_openapi_spec_async(self) -> dict[str, Any] | None:
        """Asynchronously retrieves the current Directus OpenAPI specification."""
        return await self._api.get_openapi_spec_async()

    async def get_session_async(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves detailed information about a formation session."""
        return await self._api.get_session_async(id, fields=fields)

    async def list_sessions_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists formation sessions."""
        return await self._api.list_sessions_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def get_genius_sport_match_async(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves detailed Genius Sports match statistics."""
        return await self._api.get_genius_sport_match_async(id, fields=fields)

    async def list_genius_sport_matches_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Genius Sports match statistics."""
        return await self._api.list_genius_sport_matches_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def list_genius_sports_live_logs_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Genius Sports live logs."""
        return await self._api.list_genius_sports_live_logs_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def get_rematch_video_async(
        self, id: str, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves a Rematch video linked to FFBB data."""
        return await self._api.get_rematch_video_async(id, fields=fields)

    async def list_rematch_videos_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Rematch videos linked to FFBB data."""
        return await self._api.list_rematch_videos_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def get_edf_match_async(
        self, id: str | int, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves an Equipe de France match."""
        return await self._api.get_edf_match_async(id, fields=fields)

    async def list_edf_matches_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Equipe de France matches."""
        return await self._api.list_edf_matches_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def get_edf_player_async(
        self, id: str | int, fields: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves an Equipe de France player."""
        return await self._api.get_edf_player_async(id, fields=fields)

    async def list_edf_players_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Equipe de France players."""
        return await self._api.list_edf_players_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def list_edf_teams_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Equipe de France teams."""
        return await self._api.list_edf_teams_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    async def list_edf_rosters_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Equipe de France rosters."""
        return await self._api.list_edf_rosters_async(
            limit=limit, fields=fields, filter_criteria=filter_criteria, sort=sort
        )

    # ------------------------------------------------------------------
    # Directus list delegations (typed)
    # ------------------------------------------------------------------

    def list_rencontres(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetRencontreResponse]:
        return self._api.list_rencontres(  # type: ignore[no-any-return]
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
        return self._api.list_salles(  # type: ignore[no-any-return]
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
        return self._api.list_terrains(  # type: ignore[no-any-return]
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
        return self._api.list_tournois(  # type: ignore[no-any-return]
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
        return self._api.list_engagements(  # type: ignore[no-any-return]
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
        return self._api.list_formations(  # type: ignore[no-any-return]
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
        return self._api.list_entraineurs(  # type: ignore[no-any-return]
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
        return self._api.list_communes(  # type: ignore[no-any-return]
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
        return self._api.list_officiels(  # type: ignore[no-any-return]
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
        return self._api.list_pratiques(  # type: ignore[no-any-return]
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
        return await self._api.list_rencontres_async(  # type: ignore[no-any-return]
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
        return await self._api.list_salles_async(  # type: ignore[no-any-return]
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
        return await self._api.list_terrains_async(  # type: ignore[no-any-return]
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
        return await self._api.list_tournois_async(  # type: ignore[no-any-return]
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
        return await self._api.list_engagements_async(  # type: ignore[no-any-return]
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
        return await self._api.list_formations_async(  # type: ignore[no-any-return]
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
        return await self._api.list_entraineurs_async(  # type: ignore[no-any-return]
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
        return await self._api.list_communes_async(  # type: ignore[no-any-return]
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
        return await self._api.list_officiels_async(  # type: ignore[no-any-return]
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
        return await self._api.list_pratiques_async(  # type: ignore[no-any-return]
            limit=limit,
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            offset=validate_offset(offset),
            search=validate_search_query(search, "search"),
            cached_session=cached_session,
        )

    # ------------------------------------------------------------------
    # list_all delegations
    # ------------------------------------------------------------------

    def list_all_rencontres(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetRencontreResponse]:
        return self._api.list_all_rencontres(  # type: ignore[no-any-return]
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
        return self._api.list_all_salles(  # type: ignore[no-any-return]
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
        return self._api.list_all_terrains(  # type: ignore[no-any-return]
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
        return self._api.list_all_tournois(  # type: ignore[no-any-return]
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
        return self._api.list_all_engagements(  # type: ignore[no-any-return]
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
        return self._api.list_all_formations(  # type: ignore[no-any-return]
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
        return self._api.list_all_entraineurs(  # type: ignore[no-any-return]
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
        return self._api.list_all_communes(  # type: ignore[no-any-return]
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
        return self._api.list_all_officiels(  # type: ignore[no-any-return]
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
        return self._api.list_all_pratiques(  # type: ignore[no-any-return]
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
        return await self._api.list_all_rencontres_async(  # type: ignore[no-any-return]
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
        return await self._api.list_all_salles_async(  # type: ignore[no-any-return]
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
        return await self._api.list_all_terrains_async(  # type: ignore[no-any-return]
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
        return await self._api.list_all_tournois_async(  # type: ignore[no-any-return]
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
        return await self._api.list_all_engagements_async(  # type: ignore[no-any-return]
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
        return await self._api.list_all_formations_async(  # type: ignore[no-any-return]
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
        return await self._api.list_all_entraineurs_async(  # type: ignore[no-any-return]
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
        return await self._api.list_all_communes_async(  # type: ignore[no-any-return]
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
        return await self._api.list_all_officiels_async(  # type: ignore[no-any-return]
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
        return await self._api.list_all_pratiques_async(  # type: ignore[no-any-return]
            filter_criteria=validate_filter_criteria(
                filter_criteria, "filter_criteria"
            ),
            sort=validate_string_list(sort, "sort"),
            search=validate_search_query(search, "search"),
            page_size=page_size,
            max_items=max_items,
            cached_session=cached_session,
        )

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

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

    async def list_engagements_by_ids_async(
        self, ids: list[int], cached_session: httpx.AsyncClient | None = None
    ) -> list[GetEngagementResponse]:
        if not ids:
            return []
        chunks = self._chunked(ids, self._BATCH_CHUNK_SIZE)
        tasks = [
            self.list_engagements_async(
                limit=len(chunk),
                filter_criteria=json.dumps({"id": {"_in": chunk}}),
                cached_session=cached_session,
            )
            for chunk in chunks
        ]
        chunk_results = await asyncio.gather(*tasks)
        results: list[GetEngagementResponse] = []
        for chunk_res in chunk_results:
            if chunk_res:
                results.extend(chunk_res)
        return results

    async def list_engagements_by_poule_async(
        self, poule_id: int, cached_session: httpx.AsyncClient | None = None
    ) -> list[GetEngagementResponse]:
        return await self.list_engagements_async(
            limit=250,
            filter_criteria=json.dumps({"idPoule": {"_eq": poule_id}}),
            cached_session=cached_session,
        )

    async def list_engagements_by_poules_async(
        self, poule_ids: list[int], cached_session: httpx.AsyncClient | None = None
    ) -> list[GetEngagementResponse]:
        if not poule_ids:
            return []
        chunks = self._chunked(poule_ids, self._BATCH_CHUNK_SIZE)
        tasks = [
            self.list_engagements_async(
                limit=len(chunk) * 15,
                filter_criteria=json.dumps({"idPoule": {"_in": chunk}}),
                cached_session=cached_session,
            )
            for chunk in chunks
        ]
        chunk_results = await asyncio.gather(*tasks)
        results: list[GetEngagementResponse] = []
        for chunk_res in chunk_results:
            if chunk_res:
                results.extend(chunk_res)
        return results

    async def list_rencontres_by_poule_async(
        self, poule_id: int, cached_session: httpx.AsyncClient | None = None
    ) -> list[GetRencontreResponse]:
        return await self.list_rencontres_async(
            limit=500,
            filter_criteria=json.dumps({"idPoule": {"_eq": poule_id}}),
            cached_session=cached_session,
        )

    async def list_rencontres_by_poules_async(
        self, poule_ids: list[int], cached_session: httpx.AsyncClient | None = None
    ) -> list[GetRencontreResponse]:
        if not poule_ids:
            return []
        chunks = self._chunked(poule_ids, self._BATCH_CHUNK_SIZE)
        tasks = [
            self.list_rencontres_async(
                limit=len(chunk) * 30,
                filter_criteria=json.dumps({"idPoule": {"_in": chunk}}),
                cached_session=cached_session,
            )
            for chunk in chunks
        ]
        chunk_results = await asyncio.gather(*tasks)
        results: list[GetRencontreResponse] = []
        for chunk_res in chunk_results:
            if chunk_res:
                results.extend(chunk_res)
        return results

    async def list_entraineurs_by_ids_async(
        self, ids: list[int], cached_session: httpx.AsyncClient | None = None
    ) -> list[GetEntraineurResponse]:
        if not ids:
            return []
        chunks = self._chunked(ids, self._BATCH_CHUNK_SIZE)
        tasks = [
            self.list_entraineurs_async(
                limit=len(chunk),
                filter_criteria=json.dumps(
                    {"idLicence": {"_in": [str(i) for i in chunk]}}
                ),
                cached_session=cached_session,
            )
            for chunk in chunks
        ]
        chunk_results = await asyncio.gather(*tasks)
        results: list[GetEntraineurResponse] = []
        for chunk_res in chunk_results:
            if chunk_res:
                results.extend(chunk_res)
        return results
