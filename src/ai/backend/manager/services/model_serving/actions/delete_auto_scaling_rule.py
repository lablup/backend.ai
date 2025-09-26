from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import RuleId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class DeleteEndpointAutoScalingRuleAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    id: RuleId

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
