import enum

__all__ = (
    "SessionGroupPlacementDirection",
    "SessionGroupPlacementEnforcement",
)


class SessionGroupPlacementDirection(enum.StrEnum):
    """How the member sessions of a group sit relative to each other, per agent."""

    SPREAD = "spread"
    PACK = "pack"
    NONE = "none"


class SessionGroupPlacementEnforcement(enum.StrEnum):
    """How hard the placement direction is enforced when it cannot be satisfied."""

    PREFERRED = "preferred"
    STRICT = "strict"
