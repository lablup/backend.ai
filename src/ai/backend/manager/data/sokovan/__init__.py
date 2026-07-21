"""Data types for Sokovan scheduler."""

from .agent import AgentInfo
from .allocation import (
    AgentAllocation,
    AllocationBatch,
    KernelAllocation,
    SchedulingFailure,
    SchedulingPredicate,
    SessionAllocation,
)
from .config import NetworkSetup
from .handler import HandlerKernelData, HandlerSessionData
from .image import ImageConfigData, ImageIdentifier
from .lifecycle import (
    KernelBindingData,
    KernelCreationInfo,
    KernelStartData,
    PreparedSessionData,
    PreparedSessionsWithImages,
    ScheduledSessionData,
    ScheduledSessionsWithImages,
    SessionDataForPull,
    SessionDataForStart,
    SessionRunningData,
    SessionsForPullWithImages,
    SessionsForStartWithImages,
    SessionWithKernels,
)
from .result import (
    KernelTerminationInfo,
    PromotionSpec,
    RetryResult,
    SchedulerExecutionError,
    SchedulerExecutionResult,
    SessionStartResult,
    SweepStaleKernelsResult,
)
from .snapshot import (
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SystemSnapshot,
)
from .workload import (
    KernelWorkload,
    SessionDependencyInfo,
    SessionWorkload,
)

__all__ = [
    # agent
    "AgentInfo",
    # allocation
    "AgentAllocation",
    "AllocationBatch",
    "KernelAllocation",
    "SchedulingFailure",
    "SchedulingPredicate",
    "SessionAllocation",
    # config
    "NetworkSetup",
    # handler
    "HandlerKernelData",
    "HandlerSessionData",
    # image
    "ImageConfigData",
    "ImageIdentifier",
    # lifecycle
    "KernelBindingData",
    "KernelCreationInfo",
    "KernelStartData",
    "PreparedSessionData",
    "PreparedSessionsWithImages",
    "ScheduledSessionData",
    "ScheduledSessionsWithImages",
    "SessionDataForPull",
    "SessionDataForStart",
    "SessionRunningData",
    "SessionsForPullWithImages",
    "SessionsForStartWithImages",
    "SessionWithKernels",
    # result
    "KernelTerminationInfo",
    "PromotionSpec",
    "RetryResult",
    "SchedulerExecutionError",
    "SchedulerExecutionResult",
    "SessionStartResult",
    "SweepStaleKernelsResult",
    # snapshot
    "ResourceOccupancySnapshot",
    "ResourcePolicySnapshot",
    "SessionDependencySnapshot",
    "SystemSnapshot",
    # workload
    "KernelWorkload",
    "SessionDependencyInfo",
    "SessionWorkload",
]
