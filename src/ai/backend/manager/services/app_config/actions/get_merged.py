"""Get merged configuration action."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config.actions.base import (
    AppConfigScopeAction,
    AppConfigScopeActionResult,
)


@dataclass
class GetMergedAppConfigAction(AppConfigScopeAction):
    """Action to get merged app configuration for a user."""

    user_id: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.user_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, self.user_id)


@dataclass
class GetMergedAppConfigActionResult(AppConfigScopeActionResult):
    """Result of get merged app configuration action."""

    user_id: str
    merged_config: Mapping[str, Any]

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.user_id
