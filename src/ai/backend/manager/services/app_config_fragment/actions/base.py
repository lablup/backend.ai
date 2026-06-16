from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.types import ActionTarget
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentKey
from ai.backend.manager.data.permission.types import RBACElementRef


@dataclass
class AppConfigFragmentAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG


@dataclass(frozen=True)
class AppConfigFragmentTarget(ActionTarget):
    """Bulk-action target identifying a fragment row by its natural key."""

    key: AppConfigFragmentKey

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.APP_CONFIG,
            element_id=f"{self.key.scope_type}:{self.key.scope_id}:{self.key.name}",
        )


@dataclass(frozen=True)
class MyAppConfigFragmentTarget(ActionTarget):
    """Bulk-action target for self-service fragments, keyed by `name`
    (the owning USER scope is resolved from the current user)."""

    name: str

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.APP_CONFIG,
            element_id=self.name,
        )
