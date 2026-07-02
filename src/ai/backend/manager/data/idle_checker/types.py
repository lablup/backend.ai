from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.types import SessionId


class ScopeType(enum.StrEnum):
    """Scope a binding attaches a checker to. Declared most- to least-specific."""

    RESOURCE_GROUP = "resource_group"
    PROJECT = "project"
    DOMAIN = "domain"


@dataclass(frozen=True)
class ScopeRef:
    """A concrete scope a binding targets (UUID-identified)."""

    scope_type: ScopeType
    scope_id: uuid.UUID


@dataclass(frozen=True)
class IdleCheckSession:
    """Session fields needed to evaluate idle checkers."""

    session_id: SessionId
    created_at: datetime
    starts_at: datetime | None
