"""Backward-compatibility re-export shim for saisons models."""

import warnings

warnings.warn(  # noqa: E402
    "Importing from 'saisons_models' is deprecated. "
    "Import directly from 'get_saisons_response' or 'saisons_query' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .get_saisons_response import GetSaisonsResponse  # noqa: E402
from .saisons_query import SaisonsQuery  # noqa: E402

__all__ = ["GetSaisonsResponse", "SaisonsQuery"]
