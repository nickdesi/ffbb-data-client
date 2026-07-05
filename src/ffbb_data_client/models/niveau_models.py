"""Backward-compatibility re-export shim for niveau module."""

import warnings

warnings.warn(  # noqa: E402
    "Importing from 'niveau_models' is deprecated. "
    "Import directly from 'niveau_type', 'niveau_info', 'niveau_extractor', "
    "or 'categorie_type' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .categorie_type import CategorieType  # noqa: E402
from .niveau_extractor import (  # noqa: E402
    NiveauExtractor,
    get_niveau_from_idcompetition,
)
from .niveau_info import NiveauInfo  # noqa: E402
from .niveau_type import NiveauType  # noqa: E402

__all__ = [
    "CategorieType",
    "NiveauExtractor",
    "NiveauInfo",
    "NiveauType",
    "get_niveau_from_idcompetition",
]
