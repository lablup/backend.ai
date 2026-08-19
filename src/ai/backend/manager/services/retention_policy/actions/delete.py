from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.services.retention_policy.actions.base import RetentionPolicyAction


@dataclass
class DeleteRetentionPolicyAction(RetentionPolicyAction):
    id: RetentionPolicyID

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteRetentionPolicyActionResult(BaseActionResult):
    policy: RetentionPolicyData

    @override
    def entity_id(self) -> str | None:
        return str(self.policy.id)
