from __future__ import annotations

from typing import Any

import httpx
from httpx import Client

from ...config import (
    ENDPOINT_COMPETITIONS,
    ENDPOINT_POULES,
    ENDPOINT_SAISONS,
)
from ...exceptions import FFBBAuthenticationError, FFBBNotFoundError
from ...helpers.http_requests_utils import http_get_json_async, url_with_params
from ...models.field_set import FieldSet
from ...models.get_competition_response import GetCompetitionResponse
from ...models.get_poule_response import GetPouleResponse
from ...models.get_saisons_response import GetSaisonsResponse
from ...models.query_fields_manager import QueryFieldsManager
from ...models.team_ranking import TeamRanking
from ...utils.secure_logging import get_secure_logger

_logger = get_secure_logger(__name__)


class CompetitionMixin:
    """Methods for competition, poule, classement, saisons."""

    url: str
    headers: dict[str, str]
    debug: bool
    async_cached_session: httpx.AsyncClient | None
    logger: Any

    def get_competition(
        self,
        competition_id: int,
        deep_limit: str | None = "1000",
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> GetCompetitionResponse | None:
        from .._helpers import run_async

        return run_async(
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
                cached_session=cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data:
                return GetCompetitionResponse.from_dict(actual_data)
            return None
        except FFBBAuthenticationError as exc:
            # BunnyCDN (WAF/HTML) : ne pas masquer par un fallback filter
            # (lui aussi bloqué) — remonter pour diagnostic CDN explicite.
            if "bunnycdn" in str(exc).lower():
                raise
            # Directus 403: direct /{id} access denied (e.g. archived season).
            # Fallback to listing with filter to distinguish "permission denied"
            # from "item purged from current dataset".
            return await self._get_competition_via_filter(
                competition_id, params, cached_session
            )
        except FFBBNotFoundError as e:
            if self.debug:
                self.logger.error(f"Error in get_competition_async: {e}")
            return None

    async def _get_competition_via_filter(
        self,
        competition_id: int,
        original_params: dict[str, Any],
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetCompetitionResponse | None:
        """Fallback: fetch a competition via listing + filter[id][_eq].

        Directus may restrict direct ``GET /items/ffbbserver_competitions/{id}``
        for items belonging to archived seasons while still exposing them through
        the collection listing endpoint.  This method transparently retries with
        ``?filter[id][_eq]=<id>&limit=1``.
        """
        _logger.info(
            "Competition %s: accès direct refusé (403), tentative via filter listing",
            competition_id,
        )
        fallback_params: dict[str, Any] = {
            k: v for k, v in original_params.items() if not k.startswith("deep[")
        }
        fallback_params["filter[id][_eq]"] = str(competition_id)
        fallback_params["limit"] = "1"

        listing_url = url_with_params(
            f"{self.url}{ENDPOINT_COMPETITIONS}", fallback_params
        )
        try:
            data = await http_get_json_async(
                listing_url,
                self.headers,
                debug=self.debug,
                cached_session=cached_session or self.async_cached_session,
            )
            items = data.get("data", []) if data and isinstance(data, dict) else []
            if items:
                return GetCompetitionResponse.from_dict(items[0])
            _logger.warning(
                "Competition %s inaccessible : saison archivée ou purgée par la FFBB.",
                competition_id,
            )
            return None
        except FFBBAuthenticationError as exc:
            # Blocage CDN sur le listing : remonter, ne pas masquer en "archivée".
            if "bunnycdn" in str(exc).lower():
                raise
            _logger.warning(
                "Fallback filter pour competition %s échoué : %s",
                competition_id,
                exc,
            )
            return None
        except Exception as exc:
            _logger.warning(
                "Fallback filter pour competition %s échoué : %s",
                competition_id,
                exc,
            )
            return None

    def get_poule(
        self,
        poule_id: int,
        deep_limit: str | None = "1000",
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> GetPouleResponse | None:
        from .._helpers import run_async

        return run_async(
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
                cached_session=cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data:
                return GetPouleResponse.from_dict(actual_data)
            return None
        except FFBBNotFoundError as e:
            if self.debug:
                self.logger.error(f"Error in get_poule_async: {e}")
            return None

    def get_classement(
        self,
        poule_id: int,
        cached_session: Client | None = None,
    ) -> list[TeamRanking] | None:
        from .._helpers import run_async

        return run_async(
            self.get_classement_async(
                poule_id, cached_session=self.async_cached_session
            )
        )

    async def get_classement_async(
        self,
        poule_id: int,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[TeamRanking] | None:
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
        from .._helpers import run_async

        return run_async(
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
                cached_session=cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data and isinstance(actual_data, list):
                return GetSaisonsResponse.from_list(actual_data)
            return []
        except FFBBNotFoundError as e:
            if self.debug:
                self.logger.error(f"Error in get_saisons_async: {e}")
            return []
