from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckerSpec
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes


@dataclass(frozen=True)
class IdleCheckSession:
    """Session fields needed to evaluate idle checkers."""

    session_id: SessionId
    created_at: datetime
    starts_at: datetime | None
    expire_at: datetime | None


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
