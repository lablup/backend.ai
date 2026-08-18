from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.entity.types import EntityData, EntityIdentifier


@dataclass(frozen=True)
class AppConfigFragmentData(EntityData):
    """Domain data for one app config fragment — a single scoped JSON document."""

    id: AppConfigFragmentID
    config_name: str
    scope_id: EntityIdentifier | None
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> AppConfigFragmentID:
        return self.id
