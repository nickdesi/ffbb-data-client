"""Backward-compatibility re-export shim for poules models."""

import warnings

warnings.warn(  # noqa: E402
    "Importing from 'poules_models' is deprecated. "
    "Import directly from 'get_poule_response' or 'poules_query' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .get_poule_response import GetPouleResponse  # noqa: E402
from .poules_query import PoulesQuery  # noqa: E402

__all__ = ["GetPouleResponse", "PoulesQuery"]
