from __future__ import annotations

from typing import Any

import httpx
from httpx import Client

from ...config import ENDPOINT_COMPETITIONS, ENDPOINT_ORGANISMES
from ...exceptions import (
    FFBBAuthenticationError,
    FFBBHTTPError,
    FFBBNotFoundError,
)
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
                cached_session=cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data:
                return GetOrganismeResponse.from_dict(actual_data)
            return None
        except FFBBNotFoundError as e:
            if self.debug:
                self.logger.error(f"Error in get_organisme_async: {e}")
            return None
        except (FFBBAuthenticationError, FFBBHTTPError) as exc:
            if self.debug:
                self.logger.warning(
                    f"Directus get_organisme_async failed ({exc}), engagement du fallback Meilisearch..."
                )
            return await self._get_organisme_meilisearch_fallback(organisme_id)

    async def _get_organisme_meilisearch_fallback(
        self, organisme_id: int | str
    ) -> GetOrganismeResponse | None:
        """Fallback résilient via Meilisearch lorsque Directus est bloqué par BunnyCDN WAF."""
        import os

        from ...config import MEILISEARCH_BASE_URL

        token = (
            os.environ.get("MEILISEARCH_BEARER_TOKEN")
            or "98f07e4d3869853c218a0f65edce2ae56cc670728d9bcb8b035a5107ce1b55dc"
        )
        url = (os.environ.get("MEILISEARCH_URL") or MEILISEARCH_BASE_URL).rstrip("/")
        org_id_str = str(organisme_id).strip()
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as http_client:
                res_org = await http_client.post(
                    f"{url}/indexes/ffbbserver_organismes/search",
                    json={"q": org_id_str, "limit": 20},
                )
                hits = (
                    res_org.json().get("hits", []) if res_org.status_code == 200 else []
                )
                org_hit = None
                for h in hits:
                    if (
                        str(h.get("id")) == org_id_str
                        or str(h.get("code", "")).upper() == org_id_str.upper()
                    ):
                        org_hit = h
                        break

                if not org_hit:
                    return None

                club_code = org_hit.get("code")
                if club_code:
                    res_eng = await http_client.post(
                        f"{url}/indexes/ffbbserver_engagements/search",
                        json={"q": club_code, "limit": 100},
                    )
                    if res_eng.status_code == 200:
                        eng_hits = res_eng.json().get("hits", [])
                        org_hit["engagements"] = [
                            e for e in eng_hits if e.get("codeClub") == club_code
                        ]

                return GetOrganismeResponse.from_dict(org_hit)
        except Exception as exc:
            if self.debug:
                self.logger.error(f"Fallback Meilisearch organisme échoué: {exc}")
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
                cached_session=cached_session or self.async_cached_session,
            )
            actual_data = data.get("data") if data and isinstance(data, dict) else data
            if actual_data and isinstance(actual_data, list):
                parsed = [
                    GetCompetitionResponse.from_dict(item)
                    for item in actual_data
                    if item
                ]
                return [p for p in parsed if p is not None]
        except FFBBNotFoundError as e:
            if self.debug:
                self.logger.error(f"Error in list_competitions_async: {e}")
        return []
