from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.manager.types import OptionalState, PartialModifier


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


@dataclass
class AppConfigModifier(PartialModifier):
    extra_config: OptionalState[dict[str, Any]] = field(
        default_factory=OptionalState[dict[str, Any]].nop
    )

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.extra_config.update_dict(to_update, "extra_config")
        return to_update
