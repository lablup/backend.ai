from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import OperationStatus

__all__ = (
    "RelationActionResultMeta",
    "RelationActionProcessResult",
)


@dataclass
class RelationActionResultMeta:
    """How a relation action run turned out.

    One outcome for the run: the operation writes one row and the scopes it was about
    are the trigger meta's.
    """

    status: OperationStatus
    description: str
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


@dataclass
class RelationActionProcessResult:
    meta: RelationActionResultMeta
