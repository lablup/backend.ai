from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from ai.backend.common.types import SessionId


class IdleCheckPhase(StrEnum):
    NOT_CHECKED = "not_checked"
    ACTIVE = "active"
    IDLE = "idle"
    IDLE_EXPIRED = "idle_expired"


class IdleJudgmentStatus(StrEnum):
    ACTIVE = "active"
    IDLE = "idle"


@dataclass(frozen=True)
class IdleCheckSession:
    """Session fields needed to evaluate idle checkers."""

    session_id: SessionId
    created_at: datetime
    starts_at: datetime | None
