from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentScopeAction,
    AppConfigFragmentScopeActionResult,
)


@dataclass
class CreateAppConfigFragmentAction(AppConfigFragmentScopeAction):
    """Admin path: create a fragment at any scope (the only path creating user-scope rows)."""

    creator_spec: AppConfigFragmentCreatorSpec

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, "")


@dataclass
class CreateAppConfigFragmentActionResult(AppConfigFragmentScopeActionResult):
    fragment: AppConfigFragmentData

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""
