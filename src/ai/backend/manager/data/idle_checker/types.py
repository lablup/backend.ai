from __future__ import annotations

import enum
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.types import SessionId


class CheckerType(enum.StrEnum):
    """Discriminator for the kind of idle checker; selects the concrete spec."""

    SESSION_LIFETIME = "session_lifetime"
    NETWORK_TIMEOUT = "network_timeout"
    UTILIZATION = "utilization"


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
class IdleCheckSessionView:
    """A session projection used by the idle-check source."""

    session_id: SessionId
    created_at: datetime
    starts_at: datetime | None
    scopes: Sequence[ScopeRef]
