from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_policy.actions.base import (
    AppConfigPolicySingleEntityAction,
    AppConfigPolicySingleEntityActionResult,
)


@dataclass
class GetAppConfigPolicyAction(AppConfigPolicySingleEntityAction):
    id: AppConfigPolicyID

    @override
    def target_entity_id(self) -> str:
        return str(self.id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.APP_CONFIG_POLICY,
            element_id=str(self.id),
        )

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetAppConfigPolicyActionResult(AppConfigPolicySingleEntityActionResult):
    policy: AppConfigPolicyData

    @override
    def target_entity_id(self) -> str:
        return str(self.policy.id)
