from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.data.entity.types import EntityData, EntityIdentifier
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironValueSource

__all__ = ("SystemSessionEnvironData",)


@dataclass(frozen=True)
class SystemSessionEnvironData(EntityData):
    id: SystemSessionEnvironID
    value_source: SystemSessionEnvironValueSource
    key: str
    scope_id: EntityIdentifier
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @override
    def entity_id(self) -> SystemSessionEnvironID:
        return self.id
