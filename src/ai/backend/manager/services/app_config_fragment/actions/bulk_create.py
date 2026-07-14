from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentBulkAction,
    AppConfigFragmentBulkActionResult,
    AppConfigFragmentBulkTarget,
)


@dataclass
class AppConfigFragmentBulkCreateItem:
    """One fragment to create; it carries no scope because all items share the action's scope."""

    config_name: str
    config: dict[str, Any]


@dataclass
class BulkCreateAppConfigFragmentAction(AppConfigFragmentBulkAction):
    """Create many fragments at one shared scope with per-item partial success."""

    scope_type: AppConfigScopeType
    scope_id: str
    items: Sequence[AppConfigFragmentBulkCreateItem]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def targets(self) -> Sequence[AppConfigFragmentBulkTarget]:
        return []


@dataclass
class BulkCreateAppConfigFragmentActionResult(AppConfigFragmentBulkActionResult):
    pass
