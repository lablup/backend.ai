from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction
from ai.backend.manager.actions.action.types import ActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentBulkActionResult,
)


@dataclass(frozen=True)
class AppConfigFragmentScopeTarget(ActionTarget):
    """One scope a bulk create writes into, exposed for per-scope RBAC.

    A ``public`` fragment is global-scoped (no RBAC scope element); its target carries the
    fragment element type with an empty id, so the bulk-scope validator treats it as a
    global target (superadmin-only).
    """

    scope_type: AppConfigScopeType
    scope_id: str

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        element = self.scope_type.to_rbac_element_type()
        if element is None:
            return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, "")
        return RBACElementRef(element, self.scope_id)


@dataclass
class BulkCreateAppConfigFragmentAction(BaseBulkAction[AppConfigFragmentScopeTarget]):
    """Create many fragments with per-item partial success; each write is authorized at its
    scope, and the FK to the allow-list gates each write."""

    creator_specs: Sequence[AppConfigFragmentCreatorSpec]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_FRAGMENT

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def targets(self) -> Sequence[AppConfigFragmentScopeTarget]:
        # Each new fragment is written at its spec's scope, so RBAC authorizes the batch per
        # scope (a public spec resolves to a global target: superadmin-only).
        return [
            AppConfigFragmentScopeTarget(scope_type=spec.scope_type, scope_id=spec.scope_id)
            for spec in self.creator_specs
        ]


@dataclass
class BulkCreateAppConfigFragmentActionResult(AppConfigFragmentBulkActionResult):
    pass
