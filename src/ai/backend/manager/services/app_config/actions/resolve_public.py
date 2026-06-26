from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config.actions.base import (
    AppConfigScopeAction,
    AppConfigScopeActionResult,
)


@dataclass
class ResolvePublicAppConfigAction(AppConfigScopeAction):
    """Anonymous (pre-login) read: merge only the ``public`` fragments of ``config_name``.

    Carries no principal — there is no domain or user, so only public-scope documents
    contribute to the merge.
    """

    config_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG, "")


@dataclass
class ResolvePublicAppConfigActionResult(AppConfigScopeActionResult):
    app_config: AppConfigData

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""
