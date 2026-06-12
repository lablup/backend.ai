import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.types import ActionTarget
from ai.backend.manager.data.permission.types import RBACElementRef


@dataclass
class AppConfigPolicyAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_POLICY


@dataclass(frozen=True)
class AppConfigPolicyTarget(ActionTarget):
    """Bulk-action target identifying an existing policy row by id."""

    id: uuid.UUID

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.APP_CONFIG_POLICY,
            element_id=str(self.id),
        )
