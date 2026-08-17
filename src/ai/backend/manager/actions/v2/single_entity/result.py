from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import OperationStatus

__all__ = (
    "SingleEntityActionResultMeta",
    "SingleEntityActionProcessResult",
)


@dataclass
class SingleEntityActionResultMeta:
    """How a single-entity action run turned out.

    What the run *is* — its id, entity, operation and name — is the trigger meta's;
    this carries only the outcome.
    """

    status: OperationStatus
    description: str
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


@dataclass
class SingleEntityActionProcessResult:
    meta: SingleEntityActionResultMeta
