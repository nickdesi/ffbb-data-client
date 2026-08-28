"""Helper modules and class extensions."""

from .http_requests_helper import catch_result
from .http_requests_utils import (
    encode_params,
    http_get,
    http_get_json,
    http_post,
    http_post_json,
    to_json_from_response,
    url_with_params,
)
from .meilisearch_client_extension import MeilisearchClientExtension
from .multi_search_query_helper import generate_queries
from .normalization import (
    ParsedCategorie,
    normalize_apostrophes,
    normalize_query,
    parse_categorie,
    strip_accents,
)

__all__ = [
    "MeilisearchClientExtension",
    "catch_result",
    "encode_params",
    "generate_queries",
    "http_get",
    "http_get_json",
    "http_post",
    "http_post_json",
    "to_json_from_response",
    "url_with_params",
    "ParsedCategorie",
    "normalize_apostrophes",
    "normalize_query",
    "parse_categorie",
    "strip_accents",
]
