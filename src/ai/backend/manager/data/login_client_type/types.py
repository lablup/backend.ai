from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.common.data.entity.types import EntityData, EntityID, EntityIdentifier

__all__ = ("LoginClientTypeData",)


@dataclass(frozen=True)
class LoginClientTypeData(EntityData):
    id: LoginClientTypeID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id
