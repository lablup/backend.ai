from dataclasses import dataclass
from typing import override

from ai.backend.common.types import RuleId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import EndpointAutoScalingRuleData
from ai.backend.manager.models.endpoint import EndpointAutoScalingRuleRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ModifyEndpointAutoScalingRuleAction(ModelServiceAction):
    id: RuleId
    updater: Updater[EndpointAutoScalingRuleRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ModifyEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool
    data: EndpointAutoScalingRuleData | None

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id) if self.data is not None else None
