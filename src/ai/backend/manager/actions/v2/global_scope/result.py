from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.exception import ErrorCode
from ai.backend.common.identifier.action import ActionID
from ai.backend.manager.actions.types import OperationStatus

__all__ = (
    "GlobalActionResultMeta",
    "GlobalActionProcessResult",
)


@dataclass
class GlobalActionResultMeta:
    """Outcome metadata for a global action run. It has no target to name."""

    action_id: ActionID
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


@dataclass
class GlobalActionProcessResult:
    meta: GlobalActionResultMeta
