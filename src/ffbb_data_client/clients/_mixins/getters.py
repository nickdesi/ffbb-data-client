from __future__ import annotations

from typing import Any

import httpx
from httpx import Client

from ...config import (
    ENDPOINT_COMMUNES,
    ENDPOINT_CONFIGURATION,
    ENDPOINT_ENGAGEMENTS,
    ENDPOINT_ENTRAINEURS,
    ENDPOINT_FORMATIONS,
    ENDPOINT_LIVES,
    ENDPOINT_OFFICIELS,
    ENDPOINT_OPENAPI,
    ENDPOINT_PRATIQUES,
    ENDPOINT_RENCONTRES,
    ENDPOINT_SALLES,
    ENDPOINT_SESSIONS,
    ENDPOINT_TERRAINS,
    ENDPOINT_TOURNOIS,
)
from ...helpers.http_requests_utils import http_get_json_async, url_with_params
from ...models.configuration_models import GetConfigurationResponse
from ...models.get_commune_response import GetCommuneResponse
from ...models.get_engagement_response import GetEngagementResponse
from ...models.get_entraineur_response import GetEntraineurResponse
from ...models.get_formation_response import GetFormationResponse
from ...models.get_officiel_response import GetOfficielResponse
from ...models.get_pratique_response import GetPratiqueResponse
from ...models.get_rencontre_response import GetRencontreResponse
from ...models.get_salle_response import GetSalleResponse
from ...models.get_terrain_response import GetTerrainResponse
from ...models.get_tournoi_response import GetTournoiResponse
from ...models.lives import Live, lives_from_dict


class GettersMixin:
    """Generic Directus fetchers + simple entity getters."""

    url: str
    headers: dict[str, str]
    debug: bool
    async_cached_session: httpx.AsyncClient | None
    retry_config: Any
    timeout_config: Any
    logger: Any

    # ------------------------------------------------------------------
    # Generic Directus helpers
    # ------------------------------------------------------------------

    def _get_directus_item(
        self,
        endpoint: str,
        id: str | int,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        from .._helpers import run_async

        return run_async(
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
        from .._helpers import run_async

        return run_async(
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

    # ------------------------------------------------------------------
    # OpenAPI
    # ------------------------------------------------------------------

    def get_openapi_spec(
        self, cached_session: Client | None = None
    ) -> dict[str, Any] | None:
        from .._helpers import run_async

        return run_async(
            self.get_openapi_spec_async(cached_session=self.async_cached_session)
        )

    async def get_openapi_spec_async(
        self, cached_session: httpx.AsyncClient | None = None
    ) -> dict[str, Any] | None:
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

    # ------------------------------------------------------------------
    # Lives
    # ------------------------------------------------------------------

    def get_lives(self, cached_session: Client | None = None) -> list[Live] | None:
        from .._helpers import run_async

        return run_async(self.get_lives_async(cached_session=self.async_cached_session))

    async def get_lives_async(
        self, cached_session: httpx.AsyncClient | None = None
    ) -> list[Live] | None:
        url = f"{self.url}{ENDPOINT_LIVES}"
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
                if isinstance(raw_data, dict) and "lives" in raw_data:
                    raw_data = raw_data["lives"]
                if not isinstance(raw_data, list):
                    return []
                return lives_from_dict(raw_data)
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_lives_async: {e}")
        return None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def get_configuration(
        self, cached_session: Client | None = None
    ) -> GetConfigurationResponse | None:
        from .._helpers import run_async

        return run_async(
            self.get_configuration_async(cached_session=self.async_cached_session)
        )

    async def get_configuration_async(
        self, cached_session: httpx.AsyncClient | None = None
    ) -> GetConfigurationResponse | None:
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

    # ------------------------------------------------------------------
    # Rencontres & Engagements
    # ------------------------------------------------------------------

    def get_rencontre(
        self, id: str, cached_session: Client | None = None
    ) -> GetRencontreResponse | None:
        from .._helpers import run_async

        return run_async(
            self.get_rencontre_async(id, cached_session=self.async_cached_session)
        )

    async def get_rencontre_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetRencontreResponse | None:
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
        from .._helpers import run_async

        return run_async(
            self.get_engagement_async(id, cached_session=self.async_cached_session)
        )

    async def get_engagement_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetEngagementResponse | None:
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

    # ------------------------------------------------------------------
    # Formations & Entraineurs
    # ------------------------------------------------------------------

    def get_formation(
        self, id: str, cached_session: Client | None = None
    ) -> GetFormationResponse | None:
        from .._helpers import run_async

        return run_async(
            self.get_formation_async(id, cached_session=self.async_cached_session)
        )

    async def get_formation_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetFormationResponse | None:
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
        from .._helpers import run_async

        return run_async(
            self.get_entraineur_async(id, cached_session=self.async_cached_session)
        )

    async def get_entraineur_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetEntraineurResponse | None:
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

    # ------------------------------------------------------------------
    # Lieux
    # ------------------------------------------------------------------

    def get_commune(
        self, id: str, cached_session: Client | None = None
    ) -> GetCommuneResponse | None:
        from .._helpers import run_async

        return run_async(
            self.get_commune_async(id, cached_session=self.async_cached_session)
        )

    async def get_commune_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetCommuneResponse | None:
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
        from .._helpers import run_async

        return run_async(
            self.get_officiel_async(id, cached_session=self.async_cached_session)
        )

    async def get_officiel_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetOfficielResponse | None:
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
        from .._helpers import run_async

        return run_async(
            self.get_salle_async(id, cached_session=self.async_cached_session)
        )

    async def get_salle_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetSalleResponse | None:
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
        from .._helpers import run_async

        return run_async(
            self.get_terrain_async(id, cached_session=self.async_cached_session)
        )

    async def get_terrain_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetTerrainResponse | None:
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
        from .._helpers import run_async

        return run_async(
            self.get_tournoi_async(id, cached_session=self.async_cached_session)
        )

    async def get_tournoi_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetTournoiResponse | None:
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
        from .._helpers import run_async

        return run_async(
            self.get_pratique_async(id, cached_session=self.async_cached_session)
        )

    async def get_pratique_async(
        self, id: str, cached_session: httpx.AsyncClient | None = None
    ) -> GetPratiqueResponse | None:
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

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def get_session(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        from .._helpers import run_async

        return run_async(
            self.get_session_async(
                id, fields=fields, cached_session=self.async_cached_session
            )
        )

    async def get_session_async(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        return await self._get_directus_item_async(
            ENDPOINT_SESSIONS,
            id,
            fields=fields,
            cached_session=self.async_cached_session,
        )

    def list_sessions(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        from .._helpers import run_async

        return run_async(
            self.list_sessions_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def list_sessions_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_directus_items_async(
            ENDPOINT_SESSIONS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )
