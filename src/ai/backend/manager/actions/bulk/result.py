import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.exception import ErrorCode
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.types import OperationStatus

__all__ = (
    "BulkActionResultMeta",
    "BulkActionProcessResult",
)


@dataclass
class BulkActionResultMeta:
    """Outcome metadata for a bulk action run.

    Self-contained for the pure-ABC bulk line; carries the ``entity_ids`` the action
    ran against because :class:`BaseBulkAction` operates on an explicit set of
    entities rather than a single identified entity.
    """

    action_id: uuid.UUID
    entity_ids: Sequence[EntityID]
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


@dataclass
class BulkActionProcessResult:
    meta: BulkActionResultMeta
