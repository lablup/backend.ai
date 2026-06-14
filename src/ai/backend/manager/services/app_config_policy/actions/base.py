from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import ActionTarget, FieldData
from ai.backend.manager.data.permission.types import RBACElementRef


@dataclass
class AppConfigPolicyAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_POLICY


@dataclass
class AppConfigPolicySingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_POLICY

    @override
    def field_data(self) -> FieldData | None:
        return None


@dataclass
class AppConfigPolicySingleEntityActionResult(BaseSingleEntityActionResult):
    pass


@dataclass(frozen=True)
class AppConfigPolicyTarget(ActionTarget):
    """Bulk-action target identifying an existing policy row by id."""

    id: AppConfigPolicyID

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.APP_CONFIG_POLICY,
            element_id=str(self.id),
        )
