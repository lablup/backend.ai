"""CreatorSpec implementations for app config entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.data.app_config.types import AppConfigScopeType
from ai.backend.manager.models.app_config import AppConfigRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class AppConfigCreatorSpec(CreatorSpec[AppConfigRow]):
    """CreatorSpec for app configurations."""

    scope_type: AppConfigScopeType
    scope_id: str
    extra_config: dict[str, Any]

    @override
    def build_row(self) -> AppConfigRow:
        return AppConfigRow(
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            extra_config=self.extra_config,
        )
