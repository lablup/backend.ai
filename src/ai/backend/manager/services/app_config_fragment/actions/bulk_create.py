from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentBulkItemError,
    AppConfigFragmentData,
    AppConfigFragmentScope,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentScopeAction,
    AppConfigFragmentScopeActionResult,
)


@dataclass
class AppConfigFragmentBulkCreateItem:
    """One fragment to create; it carries no scope because all items share the action's scope."""

    config_name: str
    config: dict[str, Any]


@dataclass
class BulkCreateAppConfigFragmentAction(AppConfigFragmentScopeAction):
    """Create many fragments at one shared scope with per-item partial success.

    The batch has one scope, so it acts at the RBAC scope of the fragments being written —
    the same scope a single create acts at — and is authorized as a scope action.
    """

    scope: AppConfigFragmentScope
    items: Sequence[AppConfigFragmentBulkCreateItem]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return self.scope.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        return self.scope.scope_type.to_rbac_scope_id(self.scope.scope_id)

    @override
    def target_element(self) -> RBACElementRef:
        element = self.scope.scope_type.to_rbac_element_type()
        if element is None:
            return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, "")
        return RBACElementRef(element, self.scope.scope_id)


@dataclass
class BulkCreateAppConfigFragmentActionResult(AppConfigFragmentScopeActionResult):
    """Partial-success result of a bulk create at one scope.

    ``succeeded`` are the created fragments; ``failed`` are the rejected items with their
    batch index and reason. The scope is the action's rather than any one fragment's, so it
    is carried here: ``succeeded`` may be empty.
    """

    scope: AppConfigFragmentScope
    succeeded: list[AppConfigFragmentData]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def scope_type(self) -> ScopeType:
        return self.scope.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        return self.scope.scope_type.to_rbac_scope_id(self.scope.scope_id)
