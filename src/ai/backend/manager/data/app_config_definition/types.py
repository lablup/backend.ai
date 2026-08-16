from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.entity.types import EntityData, EntityID


@dataclass(frozen=True)
class AppConfigDefinitionData(EntityData):
    """Domain data for an app config definition — one registered ``config_name``."""

    id: AppConfigDefinitionID
    config_name: str
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityID:
        return self.id


@dataclass(frozen=True)
class AppConfigDefinitionListResult:
    """Search result with total count for app config definitions."""

    items: list[AppConfigDefinitionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
