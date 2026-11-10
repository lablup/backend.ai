from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import OperationStatus

__all__ = (
    "MembershipActionProcessResult",
    "MembershipActionResultMeta",
)


@dataclass
class MembershipActionResultMeta:
    """How a membership action run turned out."""

    status: OperationStatus
    description: str
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


@dataclass
class MembershipActionProcessResult:
    meta: MembershipActionResultMeta
