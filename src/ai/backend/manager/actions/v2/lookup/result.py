from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.data.entity.action import ActionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import OperationStatus

__all__ = ("LookupActionResultMeta", "LookupActionProcessResult")


@dataclass
class LookupActionResultMeta:
    """Outcome metadata for a lookup action run.

    ``entity_id`` is what the key resolved to, and is absent whenever the run did not
    get that far — the key it was looking for is on the action either way.
    """

    action_id: ActionID
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None
    entity_id: EntityIdentifier | None


@dataclass
class LookupActionProcessResult:
    meta: LookupActionResultMeta
