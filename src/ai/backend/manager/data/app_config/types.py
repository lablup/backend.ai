from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override

from ai.backend.manager.models.app_config import AppConfigScopeType
from ai.backend.manager.types import Creator, OptionalState, PartialModifier


@dataclass
class MergedAppConfig:
    domain_name: str
    user_id: str
    merged_config: Mapping[str, Any]


@dataclass
class AppConfigData:
    id: int
    scope_type: AppConfigScopeType
    scope_id: str
    extra_config: dict[str, Any]
    created_at: datetime = field(compare=False)
    modified_at: datetime = field(compare=False)


@dataclass
class AppConfigCreator(Creator):
    scope_type: AppConfigScopeType
    scope_id: str
    extra_config: dict[str, Any]

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "extra_config": self.extra_config,
        }


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
