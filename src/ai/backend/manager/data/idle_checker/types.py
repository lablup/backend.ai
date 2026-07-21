from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from ai.backend.common.types import SessionId


class IdleCheckPhase(StrEnum):
    ACTIVE = "active"
    IDLE_GRACE_PERIOD = "idle_grace_period"
    IDLE_EXPIRED = "idle_expired"


@dataclass(frozen=True)
class IdleCheckSession:
    """Session fields needed to evaluate idle checkers."""

    session_id: SessionId
    created_at: datetime
    starts_at: datetime | None
