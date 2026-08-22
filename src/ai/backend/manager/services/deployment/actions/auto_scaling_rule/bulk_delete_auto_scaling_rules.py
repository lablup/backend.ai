from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.base import DeploymentGlobalAction


@dataclass
class BulkDeleteAutoScalingRulesAction(DeploymentGlobalAction):
    auto_scaling_rule_ids: list[UUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_delete_auto_scaling_rules"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class BulkDeleteAutoScalingRulesActionResult:
    deleted_ids: list[UUID]
