import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.entity.types import ScopeRef
from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import OperationStatus

__all__ = (
    "ScopeActionResultMeta",
    "ScopeActionProcessResult",
)


@dataclass
class ScopeActionResultMeta:
    """Outcome metadata for a scope action run.

    Self-contained for the pure-ABC scope line; carries the ``scope_targets`` the
    action ran against because :class:`BaseScopeAction` operates on a sequence of
    scopes rather than a single identified entity.
    """

    action_id: uuid.UUID
    scope_targets: Sequence[ScopeRef]
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


@dataclass
class ScopeActionProcessResult:
    meta: ScopeActionResultMeta
