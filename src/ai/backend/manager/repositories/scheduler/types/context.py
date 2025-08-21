"""Scheduling context data types."""

from dataclasses import dataclass

from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentInfo
from ai.backend.manager.sokovan.scheduler.types import (
    ScalingGroupInfo,
    SchedulingConfig,
    SessionWorkload,
    SystemSnapshot,
)


@dataclass
class SchedulingContextData:
    """Processed data ready for scheduling decisions."""

    scaling_group_info: ScalingGroupInfo
    pending_sessions: list[SessionWorkload]
    system_snapshot: SystemSnapshot
    scheduling_config: SchedulingConfig
    agents: list[AgentInfo]
