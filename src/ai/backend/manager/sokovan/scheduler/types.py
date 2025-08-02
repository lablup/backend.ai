from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId


@dataclass(frozen=True)
class SystemSnapshot:
    """Represents a snapshot of the system's resource state."""

    # Total resource capacity available in the Agents
    total_capacity: ResourceSlot
    # Per-user resource allocations for fairness calculation (e.g., DRF)
    # Maps access key to their total occupied resources
    user_allocations: Mapping[AccessKey, ResourceSlot]


@dataclass(frozen=True)
class SessionWorkload:
    """Represents a session workload for scheduling with minimal required fields."""

    # Session identifier
    session_id: SessionId
    # User identification for fairness calculation
    access_key: AccessKey
    # Resource requirements
    requested_slots: ResourceSlot
    # Priority level (higher value = higher priority)
    priority: int = 0


@dataclass
class AllocationSnapshot: ...
