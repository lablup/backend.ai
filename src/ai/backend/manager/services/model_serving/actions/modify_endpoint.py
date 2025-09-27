import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.modifier import EndpointModifier
from ai.backend.manager.data.model_serving.types import EndpointData, RequesterCtx
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ModifyEndpointAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    endpoint_id: uuid.UUID
    modifier: EndpointModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyEndpointActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data is not None else None
