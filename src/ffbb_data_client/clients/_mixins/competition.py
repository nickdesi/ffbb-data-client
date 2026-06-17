from __future__ import annotations

from typing import Any

import httpx
from httpx import Client

from ...config import (
    ENDPOINT_COMPETITIONS,
    ENDPOINT_POULES,
    ENDPOINT_SAISONS,
)
from ...helpers.http_requests_utils import http_get_json_async, url_with_params
from ...models.field_set import FieldSet
from ...models.get_competition_response import GetCompetitionResponse
from ...models.poules_models import GetPouleResponse
from ...models.query_fields_manager import QueryFieldsManager
from ...models.saisons_models import GetSaisonsResponse
from ...models.team_ranking import TeamRanking


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
                cached_session=self.async_cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data and isinstance(actual_data, list):
                return GetSaisonsResponse.from_list(actual_data)
            return []
        except Exception as e:
            if self.debug:
                self.logger.error(f"Error in get_saisons_async: {e}")
            return []
