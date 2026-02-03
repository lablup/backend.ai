"""Data types for Sokovan scheduler."""

from .allocation import (
    AgentAllocation,
    AllocationBatch,
    KernelAllocation,
    SchedulingFailure,
    SchedulingPredicate,
    SessionAllocation,
)
from .config import NetworkSetup, ScalingGroupInfo, SchedulingConfig
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
    KeypairOccupancy,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SystemSnapshot,
)
from .workload import (
    KernelWorkload,
    KeyPairResourcePolicy,
    PendingSessionInfo,
    SessionDependencyInfo,
    SessionWorkload,
    UserResourcePolicy,
)

__all__ = [
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
    "KeypairOccupancy",
    "PendingSessionSnapshot",
    "ResourceOccupancySnapshot",
    "ResourcePolicySnapshot",
    "SessionDependencySnapshot",
    "SystemSnapshot",
    # workload
    "KernelWorkload",
    "KeyPairResourcePolicy",
    "PendingSessionInfo",
    "SessionDependencyInfo",
    "SessionWorkload",
    "UserResourcePolicy",
]
