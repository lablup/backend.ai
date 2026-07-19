from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.retention_policy.actions.base import RetentionPolicyAction


@dataclass
class CreateRetentionPolicyAction(RetentionPolicyAction):
    creator: Creator[RetentionPolicyRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateRetentionPolicyActionResult(BaseActionResult):
    policy: RetentionPolicyData

    @override
    def entity_id(self) -> str | None:
        return str(self.policy.id)
