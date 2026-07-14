from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
)
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
    """Create a fragment at its declared scope (``public`` / ``domain`` / ``user``).

    Acts at the RBAC scope of the fragment being written, so it is not admin-only: an
    allow-listed user may create their own ``user``-scope fragment. The fragment's FK to
    the allow-list authorizes the actual write.
    """

    creator_spec: AppConfigFragmentCreatorSpec

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return self.creator_spec.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        return self.creator_spec.scope_type.to_rbac_scope_id(self.creator_spec.scope_id)

    @override
    def target_element(self) -> RBACElementRef:
        # The scope this create acts on, so RBAC checks the writer's permission there:
        # a user/domain fragment targets its USER/DOMAIN scope. A public fragment is
        # global-scoped (no RBAC scope element) and is superadmin-only — its target has
        # no scope to resolve, so a non-superadmin write fails the scope-chain check.
        element = self.creator_spec.scope_type.to_rbac_element_type()
        if element is None:
            return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, "")
        return RBACElementRef(element, self.creator_spec.scope_id)


@dataclass
class CreateAppConfigFragmentActionResult(AppConfigFragmentScopeActionResult):
    fragment: AppConfigFragmentData

    @override
    def scope_type(self) -> ScopeType:
        return self.fragment.scope_type.to_rbac_scope_type()

    @override
    def scope_id(self) -> str:
        return self.fragment.scope_type.to_rbac_scope_id(self.fragment.scope_id)
