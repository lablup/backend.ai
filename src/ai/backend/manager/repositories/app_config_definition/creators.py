"""CreatorSpec implementations for app config definition repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class AppConfigDefinitionCreatorSpec(CreatorSpec[AppConfigDefinitionRow]):
    """CreatorSpec for an app config definition."""

    config_name: str

    @override
    def build_row(self) -> AppConfigDefinitionRow:
        return AppConfigDefinitionRow(config_name=self.config_name)
