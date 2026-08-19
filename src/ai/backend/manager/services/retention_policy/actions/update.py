from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.retention_policy.actions.base import RetentionPolicyAction


@dataclass
class UpdateRetentionPolicyAction(RetentionPolicyAction):
    id: RetentionPolicyID
    updater: Updater[RetentionPolicyRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRetentionPolicyActionResult(BaseActionResult):
    policy: RetentionPolicyData

    @override
    def entity_id(self) -> str | None:
        return str(self.policy.id)
