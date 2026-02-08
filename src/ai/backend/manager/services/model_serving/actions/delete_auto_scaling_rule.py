from dataclasses import dataclass
from typing import override

from ai.backend.common.types import RuleId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class DeleteEndpointAutoScalingRuleAction(ModelServiceAction):
    id: RuleId

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
