from __future__ import annotations

from typing import Any

import httpx
from httpx import Client

from ...config import (
    ENDPOINT_EDF_MATCHES,
    ENDPOINT_EDF_PLAYERS,
    ENDPOINT_EDF_ROSTERS,
    ENDPOINT_EDF_TEAMS,
    ENDPOINT_GENIUS_SPORT_MATCHES,
    ENDPOINT_GENIUS_SPORTS_LIVE_LOGS,
    ENDPOINT_REMATCH_VIDEOS,
)
from .._helpers import run_async


class ExternalMixin:
    """Methods for external API integrations: Genius Sports, Rematch, EDF."""

    async_cached_session: httpx.AsyncClient | None
    _get_directus_item_async: Any  # Defined in GettersMixin
    _list_directus_items_async: Any  # Defined in GettersMixin

    # ------------------------------------------------------------------
    # Genius Sports
    # ------------------------------------------------------------------

    def get_genius_sport_match(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        return run_async(
            self.get_genius_sport_match_async(
                id, fields=fields, cached_session=self.async_cached_session
            )
        )

    async def get_genius_sport_match_async(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        return await self._get_directus_item_async(  # type: ignore[no-any-return]
            ENDPOINT_GENIUS_SPORT_MATCHES,
            id,
            fields=fields,
            cached_session=self.async_cached_session,
        )

    def list_genius_sport_matches(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        return run_async(
            self.list_genius_sport_matches_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def list_genius_sport_matches_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_directus_items_async(  # type: ignore[no-any-return]
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
        return run_async(
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
        return await self._list_directus_items_async(  # type: ignore[no-any-return]
            ENDPOINT_GENIUS_SPORTS_LIVE_LOGS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )

    # ------------------------------------------------------------------
    # Rematch Videos
    # ------------------------------------------------------------------

    def get_rematch_video(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        return run_async(
            self.get_rematch_video_async(
                id, fields=fields, cached_session=self.async_cached_session
            )
        )

    async def get_rematch_video_async(
        self,
        id: str,
        fields: list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        return await self._get_directus_item_async(  # type: ignore[no-any-return]
            ENDPOINT_REMATCH_VIDEOS,
            id,
            fields=fields,
            cached_session=self.async_cached_session,
        )

    def list_rematch_videos(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: Client | None = None,
    ) -> list[dict[str, Any]]:
        return run_async(
            self.list_rematch_videos_async(
                limit=limit,
                fields=fields,
                filter_criteria=filter_criteria,
                sort=sort,
                cached_session=self.async_cached_session,
            )
        )

    async def list_rematch_videos_async(
        self,
        limit: int = 10,
        fields: list[str] | None = None,
        filter_criteria: str | None = None,
        sort: str | list[str] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_directus_items_async(  # type: ignore[no-any-return]
            ENDPOINT_REMATCH_VIDEOS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )

    # ------------------------------------------------------------------
    # EDF (Equipe de France)
    # ------------------------------------------------------------------

    def get_edf_match(
        self,
        id: str | int,
        fields: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> dict[str, Any] | None:
        return run_async(
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
        return await self._get_directus_item_async(  # type: ignore[no-any-return]
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
        return run_async(
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
        return await self._list_directus_items_async(  # type: ignore[no-any-return]
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
        return run_async(
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
        return await self._get_directus_item_async(  # type: ignore[no-any-return]
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
        return run_async(
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
        return await self._list_directus_items_async(  # type: ignore[no-any-return]
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
        return run_async(
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
        return await self._list_directus_items_async(  # type: ignore[no-any-return]
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
        return run_async(
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
        return await self._list_directus_items_async(  # type: ignore[no-any-return]
            ENDPOINT_EDF_ROSTERS,
            limit=limit,
            fields=fields,
            filter_criteria=filter_criteria,
            sort=sort,
            cached_session=self.async_cached_session,
        )
