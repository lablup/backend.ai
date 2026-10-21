from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironValueSource

__all__ = ("SystemSessionEnvironData",)


@dataclass(frozen=True)
class SystemSessionEnvironData:
    id: SystemSessionEnvironID
    value_source: SystemSessionEnvironValueSource
    key: str
    scope_id: EntityIdentifier | None
    enabled: bool
    created_at: datetime
    updated_at: datetime
