from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckerSpec
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes


@dataclass(frozen=True)
class IdleCheckSession:
    """Session fields needed to evaluate idle checkers."""

    session_id: SessionId
    created_at: datetime
    starts_at: datetime | None
    expire_at: datetime | None


@dataclass(frozen=True)
class IdleCheckerAssignmentData:
    id: IdleCheckerAssignmentID
    scope_type: ScopeType
    scope_id: uuid.UUID
    idle_checker_id: IdleCheckerID
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class IdleCheckerData:
    id: IdleCheckerID
    name: str
    description: str | None
    checker_type: CheckerType
    target_session_types: list[SessionTypes]
    initial_grace_period_seconds: int
    spec: IdleCheckerSpec
    created_at: datetime
    updated_at: datetime
