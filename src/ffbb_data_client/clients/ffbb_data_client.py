from __future__ import annotations

import httpx
from httpx import Client

from ..utils.cache_manager import CacheManager
from ..utils.concurrency_utils import gather_with_concurrency
from ..utils.input_validation import validate_boolean, validate_token
from ..utils.token_manager import TokenManager
from ._helpers import run_async as _run_async
from ._rest_facade import _RestFacade
from ._search_facade import _SearchFacade
from .api_ffbb_app_client import ApiFFBBAppClient
from .meilisearch_ffbb_client import MeilisearchFFBBClient


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

    async def warm_organisme_cache_async(
        self, organisme_id: int, max_concurrency: int = 5
    ) -> None:
        """
        Pré-charge de manière asynchrone les données d'un organisme (club)
        et ses équipes dans le cache SQLite local.
        """
        await gather_with_concurrency(
            max_concurrency,
            self.get_organisme_async(organisme_id),
            self.get_equipes_async(organisme_id),
        )

    def warm_organisme_cache(self, organisme_id: int, max_concurrency: int = 5) -> None:
        """
        Pré-charge de manière synchrone les données d'un organisme (club)
        et ses équipes dans le cache SQLite local.
        """
        _run_async(self.warm_organisme_cache_async(organisme_id, max_concurrency))

    async def warm_competition_cache_async(
        self, competition_id: int, max_concurrency: int = 5
    ) -> None:
        """
        Pré-charge de manière asynchrone les données d'une compétition et de toutes
        ses poules associées dans le cache SQLite local.
        """
        comp = await self.get_competition_async(competition_id)
        if not comp:
            return

        poule_ids = set()
        if comp.poules:
            for poule in comp.poules:
                if poule.id:
                    poule_ids.add(int(poule.id))

        if comp.phases:
            for phase in comp.phases:
                if phase.poules:
                    for phase_poule in phase.poules:
                        if phase_poule.id:
                            poule_ids.add(int(phase_poule.id))

        if poule_ids:
            tasks = [self.get_poule_async(pid) for pid in sorted(poule_ids)]
            await gather_with_concurrency(max_concurrency, *tasks)

    def warm_competition_cache(
        self, competition_id: int, max_concurrency: int = 5
    ) -> None:
        """
        Pré-charge de manière synchrone les données d'une compétition et de toutes
        ses poules associées dans le cache SQLite local.
        """
        _run_async(self.warm_competition_cache_async(competition_id, max_concurrency))
