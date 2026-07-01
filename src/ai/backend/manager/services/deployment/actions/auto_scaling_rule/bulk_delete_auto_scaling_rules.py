from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.base import (
    AutoScalingRuleBaseAction,
)


@dataclass
class BulkDeleteAutoScalingRulesAction(AutoScalingRuleBaseAction):
    auto_scaling_rule_ids: list[UUID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class BulkDeleteAutoScalingRulesActionResult(BaseActionResult):
    deleted_ids: list[UUID]

    @override
    def entity_id(self) -> str | None:
        return None
