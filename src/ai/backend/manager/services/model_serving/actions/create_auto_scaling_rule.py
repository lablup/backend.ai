from dataclasses import dataclass
from typing import override

from ai.backend.common.types import EndpointId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.creator import EndpointAutoScalingRuleCreator
from ai.backend.manager.data.model_serving.types import EndpointAutoScalingRuleData
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class CreateEndpointAutoScalingRuleAction(ModelServiceAction):
    endpoint_id: EndpointId
    creator: EndpointAutoScalingRuleCreator

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool
    data: EndpointAutoScalingRuleData | None

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id) if self.data is not None else None
