from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Awaitable
from typing import Any, TypeVar

import httpx
from httpx import Client

from ..config import (
    API_FFBB_BASE_URL,
    DEFAULT_USER_AGENT,
    ENDPOINT_COMMUNES,
    ENDPOINT_COMPETITIONS,
    ENDPOINT_CONFIGURATION,
    ENDPOINT_EDF_MATCHES,
    ENDPOINT_EDF_PLAYERS,
    ENDPOINT_EDF_ROSTERS,
    ENDPOINT_EDF_TEAMS,
    ENDPOINT_ENGAGEMENTS,
    ENDPOINT_ENTRAINEURS,
    ENDPOINT_FORMATIONS,
    ENDPOINT_GENIUS_SPORT_MATCHES,
    ENDPOINT_GENIUS_SPORTS_LIVE_LOGS,
    ENDPOINT_LIVES,
    ENDPOINT_OFFICIELS,
    ENDPOINT_OPENAPI,
    ENDPOINT_ORGANISMES,
    ENDPOINT_POULES,
    ENDPOINT_PRATIQUES,
    ENDPOINT_REMATCH_VIDEOS,
    ENDPOINT_RENCONTRES,
    ENDPOINT_SAISONS,
    ENDPOINT_SALLES,
    ENDPOINT_SESSIONS,
    ENDPOINT_TERRAINS,
    ENDPOINT_TOURNOIS,
)
from ..helpers.http_requests_utils import (
    http_get_json_async,
    url_with_params,
)
from ..models.configuration_models import GetConfigurationResponse
from ..models.field_set import FieldSet
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
from ..models.lives import Live, lives_from_dict
from ..models.poules_models import GetPouleResponse
from ..models.query_fields_manager import QueryFieldsManager
from ..models.saisons_models import GetSaisonsResponse
from ..models.team_ranking import TeamRanking
from ..utils.cache_manager import CacheConfig, CacheManager
from ..utils.retry_utils import (
    RetryConfig,
    TimeoutConfig,
    get_default_retry_config,
    get_default_timeout_config,
)
from ..utils.secure_logging import get_secure_logger, mask_token

T = TypeVar("T")


def _present_items(items: list[T | None]) -> list[T]:
    return [item for item in items if item is not None]


def _run_async(coro: Awaitable[T]) -> T:
    """Run an async coroutine from sync context, handling nested event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future: concurrent.futures.Future[T] = executor.submit(asyncio.run, coro)  # type: ignore[arg-type]
            return future.result()
    elif loop:
        return loop.run_until_complete(coro)
    else:
        return asyncio.run(coro)  # type: ignore[arg-type]


class ApiFFBBAppClient:
    url: str = ""
    debug: bool = False
    headers: dict[str, str] = {}
    cached_session: Client | None = None
    async_cached_session: httpx.AsyncClient | None = None
    retry_config: RetryConfig | None = None
    timeout_config: TimeoutConfig | None = None

    def __init__(
        self,
        bearer_token: str,
        url: str = API_FFBB_BASE_URL,
        debug: bool = False,
        cached_session: Client | None = None,
        async_cached_session: httpx.AsyncClient | None = None,
        *,
        retry_config: RetryConfig | None = None,
        timeout_config: TimeoutConfig | None = None,
        cache_config: CacheConfig | None = None,
    ):
        """
        Initializes an instance of the ApiFFBBAppClient class.

        Args:
            bearer_token (str): The bearer token used for authentication.
            url (str, optional): The base URL. Defaults to "https://api.ffbb.app/".
            debug (bool, optional): Whether to enable debug mode. Defaults to False.
            cached_session (Client, optional): The cached session to use.
            retry_config (RetryConfig, optional): Retry configuration. Defaults to None.
            timeout_config (TimeoutConfig, optional): Timeout configuration.
                Defaults to None.
            cache_config (CacheConfig, optional): Cache configuration. Defaults to None.
        """
        if not bearer_token or not bearer_token.strip():
            raise ValueError("bearer_token cannot be None, empty, or whitespace-only")

        # Store token securely (private attribute)
        self._bearer_token = bearer_token
        self.url = url
        self.debug = debug
        self.cached_session = cached_session
        self.headers = {
            "Authorization": f"Bearer {self._bearer_token}",
            "user-agent": DEFAULT_USER_AGENT,
        }

        # Configure retry and timeout settings
        self.retry_config = retry_config or get_default_retry_config()
        self.timeout_config = timeout_config or get_default_timeout_config()

        # Configure cache manager
        self.cache_manager = CacheManager(cache_config)

        if cached_session is None:
            self.cached_session = self.cache_manager.session
        else:
            self.cached_session = cached_session

        if async_cached_session is None:
            self.async_cached_session = self.cache_manager.async_session
        else:
            self.async_cached_session = async_cached_session

        # Initialize secure logger
        self.logger = get_secure_logger(f"{self.__class__.__name__}")

        # Log initialization with masked token
        masked_token = mask_token(self._bearer_token)
        if self.debug:
            self.logger.info(f"ApiFFBBAppClient initialized with token: {masked_token}")
            self.logger.info(
                f"Retry config: {self.retry_config.max_attempts} attempts, "
                f"timeout: {self.timeout_config.total_timeout}s"
            )
        else:
            self.logger.info("ApiFFBBAppClient initialized successfully")

    @property
    def bearer_token(self) -> str:
        """Get the bearer token."""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth.removeprefix("Bearer ")
        return self._bearer_token

    def get_organisme_for_search(
        self,
        organisme_id: int,
        cached_session: Client | None = None,
    ) -> GetOrganismeResponse | None:
        """Version allégée de get_organisme() pour les contextes de recherche.
        Retourne 31 champs au lieu de 77 (exclut membres, labellisation, salle).
        """
        return _run_async(
            self.get_organisme_for_search_async(
                organisme_id, cached_session=self.async_cached_session
            )
        )

    async def get_organisme_for_search_async(
        self,
        organisme_id: int,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetOrganismeResponse | None:
        """Version async allégée de get_organisme() pour les contextes de recherche."""
        return await self.get_organisme_async(
            organisme_id=organisme_id,
            fields=QueryFieldsManager.get_organisme_search_fields(),
            cached_session=self.async_cached_session,
        )

    def _get_directus_item(
        self,
        endpoint: str,
        id: str | int,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        return _run_async(
            self._get_directus_item_async(
                endpoint, id, fields=fields, cached_session=self.async_cached_session
            )
        )

    async def _get_directus_item_async(
        self,
        endpoint: str,
        id: str | int,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        url = f"{self.url}{endpoint}/{id}"
        params: dict[str, Any] = {}
        if fields:
            params["fields[]"] = fields
        final_url = url_with_params(url, params) if params else url
        try:
            data = await http_get_json_async(
                final_url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
                retry_config=self.retry_config,
                timeout_config=self.timeout_config,
            )
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in _get_directus_item_async: {e}")
            return None
        actual_data = data.get("data") if data and isinstance(data, dict) else data
        return actual_data if isinstance(actual_data, dict) else None

    def _list_directus_items(
        self,
        endpoint: str,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        return _run_async(
            self._list_directus_items_async(
                endpoint,
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
        )

    async def _list_directus_items_async(
        self,
        endpoint: str,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        url = f"{self.url}{endpoint}"
        params: dict[str, Any] = {"limit": str(limit)}
        if fields:
            params["fields[]"] = fields
        if filter_criteria:
            params["filter"] = filter_criteria
        if sort:
            params["sort"] = sort
        if offset:
            params["offset"] = str(offset)
        if search:
            params["search"] = search
        final_url = url_with_params(url, params)
        try:
            data = await http_get_json_async(
                final_url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
                retry_config=self.retry_config,
                timeout_config=self.timeout_config,
            )
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in _list_directus_items_async: {e}")
            return []
        actual_data = data.get("data") if data and isinstance(data, dict) else data
        return actual_data if isinstance(actual_data, list) else []

    def get_openapi_spec(
        self, cached_session: Client | None = None
    ) -> dict[str, Any] | None:
        """Retrieves the public Directus OpenAPI specification."""
        return _run_async(
            self.get_openapi_spec_async(cached_session=self.async_cached_session)
        )

    async def get_openapi_spec_async(
        self, cached_session: httpx.AsyncClient | None = None
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves the public Directus OpenAPI specification."""
        url = f"{self.url}{ENDPOINT_OPENAPI}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
                retry_config=self.retry_config,
                timeout_config=self.timeout_config,
            )
            return data if isinstance(data, dict) else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_openapi_spec_async: {e}")
            return None

    def get_lives(self, cached_session: Client | None = None) -> list[Live] | None:
        """
        Retrieves a list of live events with retry logic.

        Args:
            cached_session (Client, optional): The cached session to use

        Returns:
            List[Live]: A list of Live objects representing the live events.
        """
        return _run_async(
            self.get_lives_async(cached_session=self.async_cached_session)
        )

    async def get_lives_async(
        self, cached_session: httpx.AsyncClient | None = None
    ) -> list[Live] | None:
        """
        Retrieves a list of live events asynchroniously.
        """
        url = f"{self.url}{ENDPOINT_LIVES}"

        # Note: catch_result is not async-friendly, but http_get_json_async handles some errors
        # In a real async environment, we might want an async_catch_result
        try:
            raw_data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
                retry_config=self.retry_config,
                timeout_config=self.timeout_config,
            )
            if raw_data is not None:
                # data might be a list or a dict with "lives" key
                if isinstance(raw_data, dict) and "lives" in raw_data:
                    raw_data = raw_data["lives"]

                if not isinstance(raw_data, list):
                    return []

                return lives_from_dict(raw_data)
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_lives_async: {e}")
        return None

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
            fields (List[str], optional): List of fields to retrieve.
                If None, uses default fields.
            cached_session (Client, optional): The cached session to use

        Returns:
            GetCompetitionResponse: Competition data with nested phases,
                poules, and rencontres
        """
        return _run_async(
            self.get_competition_async(
                competition_id,
                deep_limit=deep_limit,
                fields=fields,
                cached_session=self.async_cached_session,
            )
        )

    async def get_competition_async(
        self,
        competition_id: int,
        deep_limit: str | None = "1000",
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetCompetitionResponse | None:
        """
        Retrieves detailed information about a competition asynchroniously.
        """
        url = f"{self.url}{ENDPOINT_COMPETITIONS}/{competition_id}"

        params: dict[str, Any] = {}
        if deep_limit:
            params["deep[phases][poules][rencontres][_limit]"] = deep_limit

        if fields:
            for field in fields:
                if "fields[]" not in params:
                    params["fields[]"] = []
                params["fields[]"].append(field)
        else:
            params["fields[]"] = QueryFieldsManager.get_competition_fields(
                FieldSet.DEFAULT
            )

        final_url = url_with_params(url, params)
        try:
            data = await http_get_json_async(
                final_url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data:
                return GetCompetitionResponse.from_dict(actual_data)
            return None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_competition_async: {e}")
            return None

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
            fields (List[str], optional): List of fields to retrieve.
                If None, uses default fields.
            cached_session (Client, optional): The cached session to use

        Returns:
            GetPouleResponse: Poule data with rencontres
        """
        return _run_async(
            self.get_poule_async(
                poule_id,
                deep_limit=deep_limit,
                fields=fields,
                cached_session=self.async_cached_session,
            )
        )

    async def get_poule_async(
        self,
        poule_id: int,
        deep_limit: str | None = "1000",
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetPouleResponse | None:
        """
        Retrieves detailed information about a poule asynchroniously.
        """
        url = f"{self.url}{ENDPOINT_POULES}/{poule_id}"

        params: dict[str, Any] = {}
        if deep_limit:
            params["deep[rencontres][_limit]"] = deep_limit
            params["deep[classements][_limit]"] = deep_limit

        if fields:
            params["fields[]"] = fields
        else:
            params["fields[]"] = QueryFieldsManager.get_poule_fields(FieldSet.DEFAULT)

        final_url = url_with_params(url, params)
        try:
            data = await http_get_json_async(
                final_url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data:
                return GetPouleResponse.from_dict(actual_data)
            return None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_poule_async: {e}")
            return None

    def get_classement(
        self,
        poule_id: int,
        cached_session: Client | None = None,
    ) -> list[TeamRanking] | None:
        """
        Retrieves ONLY the ranking (classement) for a specific poule.
        """
        return _run_async(
            self.get_classement_async(
                poule_id, cached_session=self.async_cached_session
            )
        )

    async def get_classement_async(
        self,
        poule_id: int,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[TeamRanking] | None:
        """
        Asynchronously retrieves ONLY the ranking (classement) for a specific poule.
        """
        res = await self.get_poule_async(
            poule_id=poule_id,
            deep_limit="1000",
            fields=QueryFieldsManager.get_classement_fields(),
            cached_session=self.async_cached_session,
        )
        return res.classements if res else None

    def get_saisons(
        self,
        fields: list[str] | None = None,
        filter_criteria: str | None = '{"actif":{"_eq":true}}',
        cached_session: Client | None = None,
    ) -> list[GetSaisonsResponse]:
        """
        Retrieves list of seasons.

        Args:
            fields (List[str], optional): List of fields to retrieve.
                If None, uses default fields.
            filter_criteria (str, optional): JSON filter criteria.
                Defaults to active seasons.
            cached_session (Client, optional): The cached session to use

        Returns:
            List[GetSaisonsResponse]: List of season data
        """
        return _run_async(
            self.get_saisons_async(
                fields=fields,
                filter_criteria=filter_criteria,
                cached_session=self.async_cached_session,
            )
        )

    async def get_saisons_async(
        self,
        fields: list[str] | None = None,
        filter_criteria: str | None = '{"actif":{"_eq":true}}',
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetSaisonsResponse]:
        """
        Retrieves list of seasons asynchroniously.
        """
        url = f"{self.url}{ENDPOINT_SAISONS}"

        params: dict[str, Any] = {}
        if fields:
            params["fields[]"] = fields
        else:
            params["fields[]"] = QueryFieldsManager.get_saison_fields(FieldSet.DEFAULT)

        if filter_criteria:
            params["filter"] = filter_criteria

        final_url = url_with_params(url, params)
        try:
            data = await http_get_json_async(
                final_url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data and isinstance(actual_data, list):
                return GetSaisonsResponse.from_list(actual_data)
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_saisons_async: {e}")
        return []

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
            fields (List[str], optional): List of fields to retrieve.
                If None, uses default fields.
            cached_session (Client, optional): The cached session to use

        Returns:
            GetOrganismeResponse: Organisme data with members, competitions, etc.
        """
        return _run_async(
            self.get_organisme_async(
                organisme_id,
                fields=fields,
                cached_session=self.async_cached_session,
            )
        )

    async def get_organisme_async(
        self,
        organisme_id: int,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetOrganismeResponse | None:
        """
        Retrieves detailed information about an organisme asynchroniously.
        """
        url = f"{self.url}{ENDPOINT_ORGANISMES}/{organisme_id}"

        params: dict[str, Any] = {}
        if fields:
            params["fields[]"] = fields
        else:
            params["fields[]"] = QueryFieldsManager.get_organisme_fields(
                FieldSet.DEFAULT
            )

        final_url = url_with_params(url, params)
        try:
            data = await http_get_json_async(
                final_url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data:
                return GetOrganismeResponse.from_dict(actual_data)
            return None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_organisme_async: {e}")
            return None

    def get_equipes(
        self,
        organisme_id: int,
        cached_session: Client | None = None,
    ) -> list[GetOrganismeResponse.EngagementsitemModel] | None:
        """
        Retrieves ONLY the team commitments (engagements) for a specific club.
        """
        return _run_async(
            self.get_equipes_async(
                organisme_id, cached_session=self.async_cached_session
            )
        )

    async def get_equipes_async(
        self,
        organisme_id: int,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetOrganismeResponse.EngagementsitemModel] | None:
        """
        Asynchronously retrieves ONLY the team commitments (engagements) for a specific club.
        """
        res = await self.get_organisme_async(
            organisme_id=organisme_id,
            fields=QueryFieldsManager.get_equipes_fields(),
            cached_session=self.async_cached_session,
        )
        return res.engagements if res else None

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
        return _run_async(
            self.list_competitions_async(
                limit=limit,
                fields=fields,
                cached_session=self.async_cached_session,
            )
        )

    async def list_competitions_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetCompetitionResponse]:
        """
        Lists competitions with optional field selection asynchroniously.
        """
        url = f"{self.url}{ENDPOINT_COMPETITIONS}"

        params: dict[str, Any] = {"limit": str(limit)}

        if fields:
            params["fields[]"] = fields
        else:
            params["fields[]"] = ["id", "nom"]

        final_url = url_with_params(url, params)
        try:
            data = await http_get_json_async(
                final_url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data and isinstance(actual_data, list):
                parsed = [
                    GetCompetitionResponse.from_dict(item)
                    for item in actual_data
                    if item
                ]
                return [p for p in parsed if p is not None]
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in list_competitions_async: {e}")
        return []

    def get_configuration(
        self,
        cached_session: Client | None = None,
    ) -> GetConfigurationResponse | None:
        """
        Retrieves the API configuration including bearer tokens.

        This endpoint returns configuration data including:
        - key_dh: The API bearer token for api.ffbb.app
        - key_ms: The Meilisearch bearer token for meilisearch-prod.ffbb.app

        Args:
            cached_session (Client, optional): The cached session to use

        Returns:
            GetConfigurationResponse: Configuration data with tokens
        """
        return _run_async(
            self.get_configuration_async(cached_session=self.async_cached_session)
        )

    async def get_configuration_async(
        self,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetConfigurationResponse | None:
        """
        Retrieves the API configuration including bearer tokens asynchroniously.
        """
        url = f"{self.url}{ENDPOINT_CONFIGURATION}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
                retry_config=self.retry_config,
                timeout_config=self.timeout_config,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data:
                return GetConfigurationResponse.from_dict(actual_data)
            return None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_configuration_async: {e}")
            return None

    def get_rencontre(
        self, id: str, cached_session: Client | None = None
    ) -> GetRencontreResponse | None:
        """Retrieves detailed information about a rencontre."""
        return _run_async(
            self.get_rencontre_async(id, cached_session=self.async_cached_session)
        )

    async def get_rencontre_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetRencontreResponse | None:
        """Asynchronously retrieves detailed information about a rencontre."""
        url = f"{self.url}{ENDPOINT_RENCONTRES}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetRencontreResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_rencontre_async: {e}")
            return None

    def get_engagement(
        self, id: str, cached_session: Client | None = None
    ) -> GetEngagementResponse | None:
        """Retrieves detailed information about an engagement."""
        return _run_async(
            self.get_engagement_async(id, cached_session=self.async_cached_session)
        )

    async def get_engagement_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetEngagementResponse | None:
        """Asynchronously retrieves detailed information about an engagement."""
        url = f"{self.url}{ENDPOINT_ENGAGEMENTS}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetEngagementResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_engagement_async: {e}")
            return None

    def get_formation(
        self, id: str, cached_session: Client | None = None
    ) -> GetFormationResponse | None:
        """Retrieves detailed information about a formation."""
        return _run_async(
            self.get_formation_async(id, cached_session=self.async_cached_session)
        )

    async def get_formation_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetFormationResponse | None:
        """Asynchronously retrieves detailed information about a formation."""
        url = f"{self.url}{ENDPOINT_FORMATIONS}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetFormationResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_formation_async: {e}")
            return None

    def get_entraineur(
        self, id: str, cached_session: Client | None = None
    ) -> GetEntraineurResponse | None:
        """Retrieves detailed information about an entraineur."""
        return _run_async(
            self.get_entraineur_async(id, cached_session=self.async_cached_session)
        )

    async def get_entraineur_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetEntraineurResponse | None:
        """Asynchronously retrieves detailed information about an entraineur."""
        url = f"{self.url}{ENDPOINT_ENTRAINEURS}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetEntraineurResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_entraineur_async: {e}")
            return None

    def get_commune(
        self, id: str, cached_session: Client | None = None
    ) -> GetCommuneResponse | None:
        """Retrieves detailed information about a commune."""
        return _run_async(
            self.get_commune_async(id, cached_session=self.async_cached_session)
        )

    async def get_commune_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetCommuneResponse | None:
        """Asynchronously retrieves detailed information about a commune."""
        url = f"{self.url}{ENDPOINT_COMMUNES}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetCommuneResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_commune_async: {e}")
            return None

    def get_officiel(
        self, id: str, cached_session: Client | None = None
    ) -> GetOfficielResponse | None:
        """Retrieves detailed information about an officiel."""
        return _run_async(
            self.get_officiel_async(id, cached_session=self.async_cached_session)
        )

    async def get_officiel_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetOfficielResponse | None:
        """Asynchronously retrieves detailed information about an officiel."""
        url = f"{self.url}{ENDPOINT_OFFICIELS}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetOfficielResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_officiel_async: {e}")
            return None

    def get_salle(
        self, id: str, cached_session: Client | None = None
    ) -> GetSalleResponse | None:
        """Retrieves detailed information about a salle."""
        return _run_async(
            self.get_salle_async(id, cached_session=self.async_cached_session)
        )

    async def get_salle_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetSalleResponse | None:
        """Asynchronously retrieves detailed information about a salle."""
        url = f"{self.url}{ENDPOINT_SALLES}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetSalleResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_salle_async: {e}")
            return None

    def get_terrain(
        self, id: str, cached_session: Client | None = None
    ) -> GetTerrainResponse | None:
        """Retrieves detailed information about a terrain."""
        return _run_async(
            self.get_terrain_async(id, cached_session=self.async_cached_session)
        )

    async def get_terrain_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetTerrainResponse | None:
        """Asynchronously retrieves detailed information about a terrain."""
        url = f"{self.url}{ENDPOINT_TERRAINS}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetTerrainResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_terrain_async: {e}")
            return None

    def get_tournoi(
        self, id: str, cached_session: Client | None = None
    ) -> GetTournoiResponse | None:
        """Retrieves detailed information about a tournoi."""
        return _run_async(
            self.get_tournoi_async(id, cached_session=self.async_cached_session)
        )

    async def get_tournoi_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetTournoiResponse | None:
        """Asynchronously retrieves detailed information about a tournoi."""
        url = f"{self.url}{ENDPOINT_TOURNOIS}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetTournoiResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_tournoi_async: {e}")
            return None

    def get_pratique(
        self, id: str, cached_session: Client | None = None
    ) -> GetPratiqueResponse | None:
        """Retrieves detailed information about a pratique."""
        return _run_async(
            self.get_pratique_async(id, cached_session=self.async_cached_session)
        )

    async def get_pratique_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetPratiqueResponse | None:
        """Asynchronously retrieves detailed information about a pratique."""
        url = f"{self.url}{ENDPOINT_PRATIQUES}/{id}"
        try:
            data = await http_get_json_async(
                url,
                self.headers,
                debug=self.debug,
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            return GetPratiqueResponse.from_dict(actual_data) if actual_data else None
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_pratique_async: {e}")
            return None

    def get_session(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        """Retrieves detailed information about a formation session."""
        return _run_async(
            self.get_session_async(
                id, fields=fields, cached_session=self.async_cached_session
            )
        )

    def list_sessions(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        """Lists formation sessions."""
        return _run_async(
            self.list_sessions_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def get_session_async(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves detailed information about a formation session."""
        return await self._get_directus_item_async(
            ENDPOINT_SESSIONS,
            id,
            fields=fields,
            cached_session=self.async_cached_session,
        )

    async def list_sessions_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists formation sessions."""
        return await self._list_directus_items_async(
            ENDPOINT_SESSIONS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )

    # ---------- list_rencontres ----------
    def list_rencontres(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetRencontreResponse]:
        return _run_async(
            self.list_rencontres_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_RENCONTRES,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetRencontreResponse.from_dict(r) for r in raw if r])

    # ---------- list_salles ----------
    def list_salles(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetSalleResponse]:
        return _run_async(
            self.list_salles_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_SALLES,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetSalleResponse.from_dict(r) for r in raw if r])

    # ---------- list_terrains ----------
    def list_terrains(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetTerrainResponse]:
        return _run_async(
            self.list_terrains_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_TERRAINS,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetTerrainResponse.from_dict(r) for r in raw if r])

    # ---------- list_tournois ----------
    def list_tournois(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetTournoiResponse]:
        return _run_async(
            self.list_tournois_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_TOURNOIS,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetTournoiResponse.from_dict(r) for r in raw if r])

    # ---------- list_engagements ----------
    def list_engagements(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetEngagementResponse]:
        return _run_async(
            self.list_engagements_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_ENGAGEMENTS,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetEngagementResponse.from_dict(r) for r in raw if r])

    # ---------- list_formations ----------
    def list_formations(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetFormationResponse]:
        return _run_async(
            self.list_formations_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_FORMATIONS,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetFormationResponse.from_dict(r) for r in raw if r])

    # ---------- list_entraineurs ----------
    def list_entraineurs(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetEntraineurResponse]:
        return _run_async(
            self.list_entraineurs_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_ENTRAINEURS,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetEntraineurResponse.from_dict(r) for r in raw if r])

    # ---------- list_communes ----------
    def list_communes(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetCommuneResponse]:
        return _run_async(
            self.list_communes_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_COMMUNES,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetCommuneResponse.from_dict(r) for r in raw if r])

    # ---------- list_officiels ----------
    def list_officiels(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetOfficielResponse]:
        return _run_async(
            self.list_officiels_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_OFFICIELS,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetOfficielResponse.from_dict(r) for r in raw if r])

    # ---------- list_pratiques ----------
    def list_pratiques(
        self,
        limit: int = 10,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        offset: int | None = None,
        search: str | None = None,
        cached_session: Client | None = None,
    ) -> list[GetPratiqueResponse]:
        return _run_async(
            self.list_pratiques_async(
                limit=limit,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=offset,
                search=search,
                cached_session=self.async_cached_session,
            )
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
        raw = await self._list_directus_items_async(
            ENDPOINT_PRATIQUES,
            limit=limit,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=offset,
            search=search,
            cached_session=self.async_cached_session,
        )
        return _present_items([GetPratiqueResponse.from_dict(r) for r in raw if r])

    # ---------- Pagination helper: list all items ----------
    def _list_all_directus_items(
        self,
        endpoint: str,
        model_cls,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list:
        return _run_async(
            self._list_all_directus_items_async(
                endpoint,
                model_cls,
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
        )

    def list_all_rencontres(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: Client | None = None,
    ) -> list[GetRencontreResponse]:
        return _run_async(
            self.list_all_rencontres_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
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
        return _run_async(
            self.list_all_salles_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
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
        return _run_async(
            self.list_all_terrains_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
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
        return _run_async(
            self.list_all_tournois_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
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
        return _run_async(
            self.list_all_engagements_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
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
        return _run_async(
            self.list_all_formations_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
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
        return _run_async(
            self.list_all_entraineurs_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
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
        return _run_async(
            self.list_all_communes_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
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
        return _run_async(
            self.list_all_officiels_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
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
        return _run_async(
            self.list_all_pratiques_async(
                filter_criteria=filter_criteria,
                sort=sort,
                search=search,
                page_size=page_size,
                max_items=max_items,
                cached_session=self.async_cached_session,
            )
        )

    async def _list_all_directus_items_async(
        self,
        endpoint: str,
        model_cls,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list:
        first_batch = await self._list_directus_items_async(
            endpoint,
            limit=page_size,
            filter_criteria=filter_criteria,
            sort=sort,
            offset=0,
            search=search,
            cached_session=self.async_cached_session,
        )
        if not first_batch:
            return []
        results = [model_cls.from_dict(r) for r in first_batch if r]
        if len(first_batch) < page_size or len(results) >= max_items:
            return results[:max_items]
        total_pages = min((max_items + page_size - 1) // page_size, 20)
        remaining_tasks = [
            self._list_directus_items_async(
                endpoint,
                limit=page_size,
                filter_criteria=filter_criteria,
                sort=sort,
                offset=i * page_size,
                search=search,
                cached_session=self.async_cached_session,
            )
            for i in range(1, total_pages)
        ]
        remaining_batches = await asyncio.gather(*remaining_tasks)
        for batch in remaining_batches:
            if not batch:
                break
            results.extend([model_cls.from_dict(r) for r in batch if r])
            if len(batch) < page_size:
                break
        return results[:max_items]

    async def list_all_rencontres_async(
        self,
        filter_criteria: str | None = None,
        sort: list[str] | None = None,
        search: str | None = None,
        page_size: int = 100,
        max_items: int = 10000,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetRencontreResponse]:
        return await self._list_all_directus_items_async(
            ENDPOINT_RENCONTRES,
            GetRencontreResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
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
        return await self._list_all_directus_items_async(
            ENDPOINT_SALLES,
            GetSalleResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
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
        return await self._list_all_directus_items_async(
            ENDPOINT_TERRAINS,
            GetTerrainResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
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
        return await self._list_all_directus_items_async(
            ENDPOINT_TOURNOIS,
            GetTournoiResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
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
        return await self._list_all_directus_items_async(
            ENDPOINT_ENGAGEMENTS,
            GetEngagementResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
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
        return await self._list_all_directus_items_async(
            ENDPOINT_FORMATIONS,
            GetFormationResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
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
        return await self._list_all_directus_items_async(
            ENDPOINT_ENTRAINEURS,
            GetEntraineurResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
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
        return await self._list_all_directus_items_async(
            ENDPOINT_COMMUNES,
            GetCommuneResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
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
        return await self._list_all_directus_items_async(
            ENDPOINT_OFFICIELS,
            GetOfficielResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
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
        return await self._list_all_directus_items_async(
            ENDPOINT_PRATIQUES,
            GetPratiqueResponse,
            filter_criteria=filter_criteria,
            sort=sort,
            search=search,
            page_size=page_size,
            max_items=max_items,
            cached_session=self.async_cached_session,
        )

    def get_genius_sport_match(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        """Retrieves detailed Genius Sports match statistics."""
        return _run_async(
            self.get_genius_sport_match_async(
                id, fields=fields, cached_session=self.async_cached_session
            )
        )

    def list_genius_sport_matches(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Genius Sports match statistics."""
        return _run_async(
            self.list_genius_sport_matches_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def get_genius_sport_match_async(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves detailed Genius Sports match statistics."""
        return await self._get_directus_item_async(
            ENDPOINT_GENIUS_SPORT_MATCHES,
            id,
            fields=fields,
            cached_session=self.async_cached_session,
        )

    async def list_genius_sport_matches_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Genius Sports match statistics."""
        return await self._list_directus_items_async(
            ENDPOINT_GENIUS_SPORT_MATCHES,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )

    def list_genius_sports_live_logs(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Genius Sports live logs."""
        return _run_async(
            self.list_genius_sports_live_logs_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def list_genius_sports_live_logs_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Genius Sports live logs."""
        return await self._list_directus_items_async(
            ENDPOINT_GENIUS_SPORTS_LIVE_LOGS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )

    def get_rematch_video(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        """Retrieves a Rematch video linked to FFBB data."""
        return _run_async(
            self.get_rematch_video_async(
                id, fields=fields, cached_session=self.async_cached_session
            )
        )

    def list_rematch_videos(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Rematch videos linked to FFBB data."""
        return _run_async(
            self.list_rematch_videos_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def get_rematch_video_async(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves a Rematch video linked to FFBB data."""
        return await self._get_directus_item_async(
            ENDPOINT_REMATCH_VIDEOS,
            id,
            fields=fields,
            cached_session=self.async_cached_session,
        )

    async def list_rematch_videos_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Rematch videos linked to FFBB data."""
        return await self._list_directus_items_async(
            ENDPOINT_REMATCH_VIDEOS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )

    def get_edf_match(
        self,
        id: str | int,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        """Retrieves an Equipe de France match."""
        return _run_async(
            self.get_edf_match_async(
                id, fields=fields, cached_session=self.async_cached_session
            )
        )

    async def get_edf_match_async(
        self,
        id: str | int,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves an Equipe de France match."""
        return await self._get_directus_item_async(
            ENDPOINT_EDF_MATCHES,
            id,
            fields=fields,
            cached_session=self.async_cached_session,
        )

    def list_edf_matches(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France matches."""
        return _run_async(
            self.list_edf_matches_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def list_edf_matches_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Equipe de France matches."""
        return await self._list_directus_items_async(
            ENDPOINT_EDF_MATCHES,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )

    def get_edf_player(
        self,
        id: str | int,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        """Retrieves an Equipe de France player."""
        return _run_async(
            self.get_edf_player_async(
                id, fields=fields, cached_session=self.async_cached_session
            )
        )

    async def get_edf_player_async(
        self,
        id: str | int,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        """Asynchronously retrieves an Equipe de France player."""
        return await self._get_directus_item_async(
            ENDPOINT_EDF_PLAYERS,
            id,
            fields=fields,
            cached_session=self.async_cached_session,
        )

    def list_edf_players(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France players."""
        return _run_async(
            self.list_edf_players_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def list_edf_players_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Equipe de France players."""
        return await self._list_directus_items_async(
            ENDPOINT_EDF_PLAYERS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )

    def list_edf_teams(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France teams."""
        return _run_async(
            self.list_edf_teams_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def list_edf_teams_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Equipe de France teams."""
        return await self._list_directus_items_async(
            ENDPOINT_EDF_TEAMS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )

    def list_edf_rosters(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        """Lists Equipe de France rosters."""
        return _run_async(
            self.list_edf_rosters_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def list_edf_rosters_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        """Asynchronously lists Equipe de France rosters."""
        return await self._list_directus_items_async(
            ENDPOINT_EDF_ROSTERS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )
