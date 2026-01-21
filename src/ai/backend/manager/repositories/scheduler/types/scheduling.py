"""Main scheduling data type."""

from dataclasses import dataclass
from functools import cached_property
from typing import Optional

from ai.backend.common.types import ResourceSlot

from .agent import AgentMeta
from .base import SchedulingSpec
from .scaling_group import ScalingGroupMeta
from .session import PendingSessions
from .snapshot import SnapshotData


@dataclass
class SchedulingData:
    """Complete scheduling data structure."""

    scaling_group: ScalingGroupMeta
    pending_sessions: PendingSessions
    agents: list[AgentMeta]
    snapshot_data: Optional[SnapshotData]
    spec: SchedulingSpec

    @cached_property
    def total_capacity(self) -> ResourceSlot:
        """Calculate total available capacity from all agents."""
        return sum((agent.available_slots for agent in self.agents), ResourceSlot())
