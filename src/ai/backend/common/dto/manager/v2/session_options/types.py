"""DTO-specific enums for session options.

Kept distinct from the in-memory ``manager.data.session.options`` enums
so the API surface does not import from component-specific data types
(per ``common/dto/AGENTS.md``). Values are kept in sync manually —
adapters convert between these and the data-layer counterparts.
"""

from __future__ import annotations

from enum import StrEnum


class FailurePolicyEnum(StrEnum):
    """Session-wide policy governing how a kernel group's startup
    failures affect the owning session.

    Concrete enforcement lives in a follow-up task; the DTO only
    transports the choice from clients to the scheduler's write path,
    where it is frozen onto the session snapshot.
    """

    STRICT = "strict"
    """Any single kernel failure terminates the whole session."""

    BOOT_ALL = "boot-all"
    """All replicas across all groups must successfully boot before the
    session transitions to RUNNING; a late failure still fails the
    session."""

    TOLERANT = "tolerant"
    """The session keeps running as long as at least one replica per
    group stays up; individual replica failures are logged but
    non-fatal."""


class AgentSelectionPolicyEnum(StrEnum):
    """Scheduling constraint applied to ``SchedulingTargetInput.designated_agents``."""

    STRICT = "strict"
    """Place the session only on agents listed in ``designated_agents``;
    fail the schedule attempt if none of them have capacity."""

    PREFERRED = "preferred"
    """Prefer ``designated_agents`` when they have capacity, otherwise
    fall back to any eligible agent in the resource group."""
