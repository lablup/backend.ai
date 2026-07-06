"""CreatorSpec implementations for app config fragment repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class AppConfigFragmentCreatorSpec(CreatorSpec[AppConfigFragmentRow]):
    """CreatorSpec for one app config fragment.

    The fragment carries no merge priority of its own — its rank is the ``rank`` of
    the allow-list entry for its ``(config_name, scope_type)``.
    """

    config_name: str
    scope_type: AppConfigScopeType
    scope_id: str
    config: dict[str, Any]

    @override
    def build_row(self) -> AppConfigFragmentRow:
        return AppConfigFragmentRow(
            config_name=self.config_name,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            config=self.config,
        )
