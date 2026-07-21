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
from .config import NetworkSetup, ScalingGroupInfo, SchedulingConfig
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
    AgentOccupancy,
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SystemSnapshot,
    UserSessionCounts,
)
from .workload import (
    KernelWorkload,
    PendingSessionInfo,
    SessionDependencyInfo,
    SessionWorkload,
    UserResourcePolicy,
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
    "ScalingGroupInfo",
    "SchedulingConfig",
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
    "AgentOccupancy",
    "ConcurrencySnapshot",
    "PendingSessionSnapshot",
    "ResourceOccupancySnapshot",
    "ResourcePolicySnapshot",
    "SessionDependencySnapshot",
    "SystemSnapshot",
    "UserSessionCounts",
    # workload
    "KernelWorkload",
    "PendingSessionInfo",
    "SessionDependencyInfo",
    "SessionWorkload",
    "UserResourcePolicy",
]
