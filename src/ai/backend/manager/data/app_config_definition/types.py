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
