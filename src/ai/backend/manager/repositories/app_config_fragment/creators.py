"""CreatorSpec implementations for app config fragment repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.creator import DependentCreatorSpec


@dataclass
class AppConfigFragmentCreatorSpec(DependentCreatorSpec[int, AppConfigFragmentRow]):
    """Fragment creator whose ``rank`` is assigned by the ops layer (next-value) at execution.

    ``build_row`` receives the computed next rank, so a newly created fragment is placed
    after the existing fragments for the same ``config_name``.
    """

    config_name: str
    scope_type: AppConfigScopeType
    scope_id: str
    config: dict[str, Any]

    @override
    def build_row(self, next_rank: int) -> AppConfigFragmentRow:
        return AppConfigFragmentRow(
            config_name=self.config_name,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            rank=next_rank,
            config=self.config,
        )
