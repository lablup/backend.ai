from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config.actions.base import (
    AppConfigScopeAction,
    AppConfigScopeActionResult,
)


@dataclass
class ResolveBulkAppConfigAction(AppConfigScopeAction):
    """Resolve several merged ``AppConfig``s for one ``(user, domain)`` principal at once.

    A batch over ``config_names`` for a single principal (one ``USER`` scope) — not a
    scoped search. Each name is merged independently and returned in request order.
    """

    config_names: list[str]
    domain_id: DomainID
    user_id: UserID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG, "")


@dataclass
class ResolveBulkAppConfigActionResult(AppConfigScopeActionResult):
    app_configs: list[AppConfigData]
    user_id: UserID

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)
