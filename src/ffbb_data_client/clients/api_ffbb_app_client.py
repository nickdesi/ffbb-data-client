from __future__ import annotations

import httpx
from httpx import Client

from ..config import API_FFBB_BASE_URL, DEFAULT_USER_AGENT
from ..utils.cache_manager import CacheConfig, CacheManager
from ..utils.retry_utils import (
    RetryConfig,
    TimeoutConfig,
    get_default_retry_config,
    get_default_timeout_config,
)
from ..utils.secure_logging import get_secure_logger, mask_token
from ._mixins.competition import CompetitionMixin
from ._mixins.external import ExternalMixin
from ._mixins.getters import GettersMixin
from ._mixins.list_methods import ListAllMixin, ListMixin
from ._mixins.organisme import OrganismeMixin


class ApiFFBBAppClient(
    GettersMixin,
    CompetitionMixin,
    OrganismeMixin,
    ListMixin,
    ListAllMixin,
    ExternalMixin,
):
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

        self._bearer_token = bearer_token
        self.url = url
        self.debug = debug
        self.cached_session = cached_session
        self.headers = {
            "Authorization": f"Bearer {self._bearer_token}",
            "user-agent": DEFAULT_USER_AGENT,
        }

        self.retry_config = retry_config or get_default_retry_config()
        self.timeout_config = timeout_config or get_default_timeout_config()

        self.cache_manager = CacheManager(cache_config)

        if cached_session is None:
            self.cached_session = self.cache_manager.session
        else:
            self.cached_session = cached_session

        if async_cached_session is None:
            self.async_cached_session = self.cache_manager.async_session
        else:
            self.async_cached_session = async_cached_session

        self.logger = get_secure_logger(f"{self.__class__.__name__}")

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
        return self._bearer_token


# Re-exports for backward compatibility with test mocks
from ..helpers.http_requests_utils import http_get_json_async  # noqa: E402, F401
from ..models.get_competition_response import GetCompetitionResponse  # noqa: E402, F401
from ..models.get_organisme_response import GetOrganismeResponse  # noqa: E402, F401
from ..models.lives import lives_from_dict  # noqa: E402, F401
from ..models.poules_models import GetPouleResponse  # noqa: E402, F401
from ..models.saisons_models import GetSaisonsResponse  # noqa: E402, F401
