from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config.actions.base import (
    AppConfigScopeAction,
    AppConfigScopeActionResult,
)


@dataclass
class GetAppConfigsAction(AppConfigScopeAction):
    """Get the merged ``AppConfig`` for each of ``config_names``.

    ``user_id`` is never caller-supplied — the adapter fills it from the session, so a get is
    only ever for the acting user. Unset is the anonymous, pre-login read.
    """

    config_names: list[str]
    user_id: UserID | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id) if self.user_id is not None else ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG, "")


@dataclass
class GetAppConfigsActionResult(AppConfigScopeActionResult):
    app_configs: list[AppConfigData]
    _user_id: UserID | None

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self._user_id) if self._user_id is not None else ""
