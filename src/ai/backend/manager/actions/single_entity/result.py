import uuid
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
    """Outcome metadata for a single-entity action run.

    Self-contained for the pure-ABC single-entity line; ``entity_id`` is always
    present because :class:`BaseSingleEntityAction` operates on an identified entity.
    """

    action_id: uuid.UUID
    entity_id: str
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


@dataclass
class SingleEntityActionProcessResult:
    meta: SingleEntityActionResultMeta
