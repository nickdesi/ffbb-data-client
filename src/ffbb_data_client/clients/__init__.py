"""Client classes for FFBB API interactions."""

from ._rest_facade import _RestFacade
from ._search_facade import _SearchFacade
from .api_ffbb_app_client import ApiFFBBAppClient
from .ffbb_data_client import FFBBDataClient
from .meilisearch_client import MeilisearchClient
from .meilisearch_ffbb_client import MeilisearchFFBBClient

__all__ = [
    "ApiFFBBAppClient",
    "FFBBDataClient",
    "MeilisearchClient",
    "MeilisearchFFBBClient",
    "_RestFacade",
    "_SearchFacade",
]
