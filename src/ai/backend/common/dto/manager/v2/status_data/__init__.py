"""DTO v2 for unified kernel/session status_data payload.

See https://github.com/lablup/backend.ai/issues/679 for context.
"""

from ai.backend.common.dto.manager.v2.status_data.types import (
    ErrorDetailInfo,
    KernelStatusBranch,
    KernelStatusData,
    SchedulerStatusBranch,
    SchedulingPredicateInfo,
    SessionStatusBranch,
)

__all__ = (
    "ErrorDetailInfo",
    "KernelStatusBranch",
    "KernelStatusData",
    "SchedulerStatusBranch",
    "SchedulingPredicateInfo",
    "SessionStatusBranch",
)
