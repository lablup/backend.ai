from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.app_config_policy.actions.base import AppConfigPolicyAction


@dataclass
class PurgeAppConfigPolicyAction(AppConfigPolicyAction):
    config_name: str

    @override
    def entity_id(self) -> str | None:
        return self.config_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class PurgeAppConfigPolicyActionResult(BaseActionResult):
    config_name: str
    purged: bool

    @override
    def entity_id(self) -> str | None:
        return self.config_name
