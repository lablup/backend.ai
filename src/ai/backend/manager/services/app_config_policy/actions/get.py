from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.services.app_config_policy.actions.base import AppConfigPolicyAction


@dataclass
class GetAppConfigPolicyAction(AppConfigPolicyAction):
    config_name: str

    @override
    def entity_id(self) -> str | None:
        return self.config_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetAppConfigPolicyActionResult(BaseActionResult):
    policy: AppConfigPolicyData | None

    @override
    def entity_id(self) -> str | None:
        return self.policy.config_name if self.policy is not None else None
