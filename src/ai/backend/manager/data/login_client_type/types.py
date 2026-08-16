from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.types import EntityData, EntityID

__all__ = ("LoginClientTypeData",)


@dataclass(frozen=True)
class LoginClientTypeData(EntityData):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityID:
        return self.id
