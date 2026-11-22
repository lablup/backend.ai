"""Placement policy enums shared by the agent selection and its callers."""

from __future__ import annotations

import enum


class AgentSelectionPolicy(enum.StrEnum):
    """Scheduling constraint for ``SchedulingTarget.designated_agents``."""

    STRICT = "strict"
    """Schedule only onto ``designated_agents``; fail the schedule if
    none are available."""

    PREFERRED = "preferred"
    """Prefer ``designated_agents`` but fall back to any eligible agent
    when they have no capacity."""


class SessionGroupPlacementDirection(enum.StrEnum):
    """How the member sessions of a group sit relative to each other, per agent."""

    SPREAD = "spread"
    PACK = "pack"
    NONE = "none"


class SessionGroupPlacementEnforcement(enum.StrEnum):
    """How hard the placement direction is enforced when it cannot be satisfied."""

    PREFERRED = "preferred"
    STRICT = "strict"


class SessionGroupAdmission(enum.StrEnum):
    """Whether the member sessions of a group are admitted one by one or all at once."""

    INDEPENDENT = "independent"
    ALL_OR_NONE = "all_or_none"
