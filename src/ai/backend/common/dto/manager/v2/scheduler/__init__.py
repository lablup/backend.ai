"""
Scheduler DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.scheduler.request import (
    ComputeScheduleInput,
    ComputeScheduleKernelResourceInput,
)
from ai.backend.common.dto.manager.v2.scheduler.response import (
    ComputeScheduleKernelResultInfo,
    ComputeSchedulePayload,
    SchedulingBroadcastEventPayloadNode,
    SchedulingStatusDTO,
    UnschedulableReasonHintInfo,
)

__all__ = (
    "ComputeScheduleInput",
    "ComputeScheduleKernelResourceInput",
    "ComputeScheduleKernelResultInfo",
    "ComputeSchedulePayload",
    "SchedulingBroadcastEventPayloadNode",
    "SchedulingStatusDTO",
    "UnschedulableReasonHintInfo",
)
