"""CreatorSpec implementations for app config allow-list repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.app_config_allow_list.types import AppConfigScopeType
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class AppConfigAllowListCreatorSpec(CreatorSpec[AppConfigAllowListRow]):
    """CreatorSpec for an app config allow-list entry."""

    config_name: str
    scope_type: AppConfigScopeType

    @override
    def build_row(self) -> AppConfigAllowListRow:
        return AppConfigAllowListRow(config_name=self.config_name, scope_type=self.scope_type)
