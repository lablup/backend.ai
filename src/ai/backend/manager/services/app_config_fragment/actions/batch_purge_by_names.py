from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentBatchPurgerByNamesSpec,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
)
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentScopeAction,
    AppConfigFragmentScopeActionResult,
)


@dataclass
class BatchPurgeAppConfigFragmentsByNamesAction(AppConfigFragmentScopeAction):
    """Purge the fragments one scope holds for the given config names, all-or-nothing.

    A fragment is addressed by ``(scope, config_name)``, so every name resolves at ``scope``
    and the RBAC gate is the purge permission there — the same single-scope gate the scoped
    upsert crosses, rather than the per-fragment gate a purge by id crosses.
    """

    purger_spec: AppConfigFragmentBatchPurgerByNamesSpec

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def scope_type(self) -> ScopeType:
        scope = self.purger_spec.scope
        return scope.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        scope = self.purger_spec.scope
        return scope.scope_type.to_rbac_scope_id(scope.scope_id)

    @override
    def target_element(self) -> RBACElementRef:
        scope = self.purger_spec.scope
        owner_element = scope.scope_type.to_rbac_element_type()
        if owner_element is None:
            # ``public`` is global and owns no element; only a superadmin passes.
            return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, "")
        return RBACElementRef(owner_element, str(scope.scope_id))


@dataclass
class BatchPurgeAppConfigFragmentsByNamesActionResult(AppConfigFragmentScopeActionResult):
    fragments: list[AppConfigFragmentData]
    #: The scope the purge ran at, carried only to report the RBAC scope.
    _scope: AppConfigFragmentSearchScope

    @override
    def scope_type(self) -> ScopeType:
        return self._scope.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        return self._scope.scope_type.to_rbac_scope_id(self._scope.scope_id)
