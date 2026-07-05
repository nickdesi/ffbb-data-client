"""Backward-compatibility re-export shim for GameStatsModel."""

import warnings

warnings.warn(  # noqa: E402
    "Importing from 'game_stats_models' is deprecated. "
    "Import directly from 'game_stats_model' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .game_stats_model import GameStatsModel  # noqa: E402

__all__ = ["GameStatsModel"]
