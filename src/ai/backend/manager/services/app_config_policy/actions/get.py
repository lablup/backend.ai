from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.services.app_config_policy.actions.base import AppConfigPolicyAction


@dataclass
class GetAppConfigPolicyAction(AppConfigPolicyAction):
    id: AppConfigPolicyID

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetAppConfigPolicyActionResult(BaseActionResult):
    policy: AppConfigPolicyData | None

    @override
    def entity_id(self) -> str | None:
        return str(self.policy.id) if self.policy is not None else None
