from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import (
    ModelDeploymentAutoScalingRuleData,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.base import (
    AutoScalingRuleBaseAction,
)


@dataclass
class BatchLoadAutoScalingRulesAction(AutoScalingRuleBaseAction):
    auto_scaling_rule_ids: list[UUID]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "batch_load_auto_scaling_rules"


@dataclass
class BatchLoadAutoScalingRulesActionResult(BaseActionResult):
    data: list[ModelDeploymentAutoScalingRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
