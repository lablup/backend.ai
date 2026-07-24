from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.app_config_fragment.upserters import (
    AppConfigFragmentUpserterSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentScopeAction,
    AppConfigFragmentScopeActionResult,
)


@dataclass
class UpsertAppConfigFragmentsAction(AppConfigFragmentScopeAction):
    """Upsert many fragments at one scope (RBAC-authorized at that scope).

    Every item shares ``scope``, so the RBAC gate is the write permission at that single
    scope — the same gate a create at that scope crosses.
    """

    scope: AppConfigFragmentSearchScope
    upserter_specs: list[AppConfigFragmentUpserterSpec]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        # Upsert may insert, so it requires the create permission at the scope.
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return self.scope.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        return self.scope.scope_type.to_rbac_scope_id(self.scope.scope_id)

    @override
    def target_element(self) -> RBACElementRef:
        owner_element = self.scope.scope_type.to_rbac_element_type()
        if owner_element is None:
            # ``public`` is global and owns no element; only a superadmin passes.
            return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, "")
        return RBACElementRef(owner_element, str(self.scope.scope_id))


@dataclass
class UpsertAppConfigFragmentsActionResult(AppConfigFragmentScopeActionResult):
    fragments: list[AppConfigFragmentData]
    #: The scope the upsert ran at, carried only to report the RBAC scope.
    _scope: AppConfigFragmentSearchScope

    @override
    def scope_type(self) -> ScopeType:
        return self._scope.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        return self._scope.scope_type.to_rbac_scope_id(self._scope.scope_id)
