"""Backward-compatibility re-export shim for RankingEngagement, TeamRanking."""

import warnings

warnings.warn(  # noqa: E402
    "Importing from 'rankings_models' is deprecated. "
    "Import directly from 'ranking_engagement' or 'team_ranking' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .ranking_engagement import RankingEngagement  # noqa: E402
from .team_ranking import TeamRanking  # noqa: E402

__all__ = ["RankingEngagement", "TeamRanking"]
