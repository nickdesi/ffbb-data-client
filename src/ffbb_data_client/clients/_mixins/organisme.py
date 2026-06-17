from __future__ import annotations

from typing import Any

import httpx
from httpx import Client

from ...config import ENDPOINT_COMPETITIONS, ENDPOINT_ORGANISMES
from ...helpers.http_requests_utils import http_get_json_async, url_with_params
from ...models.field_set import FieldSet
from ...models.get_competition_response import GetCompetitionResponse
from ...models.get_organisme_response import GetOrganismeResponse
from ...models.query_fields_manager import QueryFieldsManager


class OrganismeMixin:
    """Methods for organisme, equipes, list_competitions."""

    url: str
    headers: dict[str, str]
    debug: bool
    async_cached_session: httpx.AsyncClient | None
    logger: Any

    def get_organisme_for_search(
        self,
        organisme_id: int,
        cached_session: Client | None = None,
    ) -> GetOrganismeResponse | None:
        from .._helpers import run_async

        return run_async(
            self.get_organisme_for_search_async(
                organisme_id=organisme_id,
                cached_session=self.async_cached_session,
            )
        )

    async def get_organisme_for_search_async(
        self,
        organisme_id: int,
        cached_session: httpx.AsyncClient | None = None,
    ) -> GetOrganismeResponse | None:
        return await self.get_organisme_async(
            organisme_id=organisme_id,
            fields=QueryFieldsManager.get_organisme_search_fields(),
            cached_session=self.async_cached_session,
        )

    def get_organisme(
        self,
        organisme_id: int,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> GetOrganismeResponse | None:
        from .._helpers import run_async

        return run_async(
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
        from .._helpers import run_async

        return run_async(
            self.get_equipes_async(
                organisme_id, cached_session=self.async_cached_session
            )
        )

    async def get_equipes_async(
        self,
        organisme_id: int,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[GetOrganismeResponse.EngagementsitemModel] | None:
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
        from .._helpers import run_async

        return run_async(
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
