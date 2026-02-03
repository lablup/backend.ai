from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


class AppConfigScopeType(enum.StrEnum):
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"


@dataclass
class MergedAppConfig:
    domain_name: str
    user_id: str
    merged_config: Mapping[str, Any]


@dataclass
class AppConfigData:
    id: UUID
    scope_type: AppConfigScopeType
    scope_id: str
    extra_config: dict[str, Any]
    created_at: datetime = field(compare=False)
    modified_at: datetime = field(compare=False)
