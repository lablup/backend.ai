from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.types import AppConfigScopeArguments
from ai.backend.manager.services.app_config.actions.base import (
    AppConfigScopeAction,
    AppConfigScopeActionResult,
)


@dataclass
class ResolveBulkAppConfigAction(AppConfigScopeAction):
    """Resolve several merged ``AppConfig``s for one principal at once.

    ``scope`` carries the resolving principal ``(user, domain)``. When it is ``None`` — the
    anonymous, pre-login read — only ``public``-scope fragments contribute; the action stays
    a ``USER``-scope read but carries no ``scope_id``.
    """

    config_names: list[str]
    scope: AppConfigScopeArguments | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.scope.user_id) if self.scope is not None else ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG, "")


@dataclass
class ResolveBulkAppConfigActionResult(AppConfigScopeActionResult):
    app_configs: list[AppConfigData]
    _user_id: UserID | None

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self._user_id) if self._user_id is not None else ""
