from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class AppConfigScopeType(enum.StrEnum):
    PUBLIC = "public"
    DOMAIN = "domain"
    DOMAIN_USER_DEFAULTS = "domain_user_defaults"
    USER = "user"


@dataclass(frozen=True, slots=True)
class AppConfigFragmentKey:
    """Natural-key identifier for a single `app_config_fragments` row."""

    scope_type: AppConfigScopeType
    scope_id: str
    name: str


@dataclass(frozen=True)
class AppConfigFragmentData:
    id: uuid.UUID
    scope_type: AppConfigScopeType
    scope_id: str
    name: str
    extra_config: Mapping[str, Any]
    created_at: datetime
    updated_at: datetime

    @property
    def key(self) -> AppConfigFragmentKey:
        return AppConfigFragmentKey(
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            name=self.name,
        )
