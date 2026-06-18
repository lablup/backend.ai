from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID


@dataclass(frozen=True)
class AppConfigDefinitionData:
    """Domain data for an app config definition — one registered ``config_name``."""

    id: AppConfigDefinitionID
    config_name: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AppConfigDefinitionListResult:
    """Search result with total count for app config definitions."""

    items: list[AppConfigDefinitionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
