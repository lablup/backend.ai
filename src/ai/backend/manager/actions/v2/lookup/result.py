from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.exception import ErrorCode
from ai.backend.common.identifier.action import ActionID
from ai.backend.manager.actions.types import OperationStatus

__all__ = ("LookupActionResultMeta", "LookupActionProcessResult")


@dataclass
class LookupActionResultMeta:
    """Outcome metadata for a lookup action run.

    There is no target to name: until the run succeeds the id does not exist, and the
    key it was looking for is on the action.
    """

    action_id: ActionID
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


@dataclass
class LookupActionProcessResult:
    meta: LookupActionResultMeta
