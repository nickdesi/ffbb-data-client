from enum import Enum


class TournoisHitType(Enum):
    TERRAIN = "Terrain"


# Backward-compatible alias
HitType = TournoisHitType
