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
    ResourceGroupUnschedulableReasonDTO,
    SchedulingBroadcastEventPayloadNode,
    SchedulingStatusDTO,
    UnschedulableReasonHintInfo,
)

__all__ = (
    "ComputeScheduleInput",
    "ComputeScheduleKernelResourceInput",
    "ComputeScheduleKernelResultInfo",
    "ComputeSchedulePayload",
    "ResourceGroupUnschedulableReasonDTO",
    "SchedulingBroadcastEventPayloadNode",
    "SchedulingStatusDTO",
    "UnschedulableReasonHintInfo",
)
