import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import (
    ModelServiceAction,
)
from ai.backend.manager.services.model_service.types import (
    EndpointAutoScalingRuleCreator,
    EndpointAutoScalingRuleData,
    EndpointAutoScalingRuleModifier,
    RequesterCtx,
)


@dataclass
class CreateEndpointAutoScalingRuleAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    endpoint_id: uuid.UUID
    creator: EndpointAutoScalingRuleCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"


@dataclass
class ModifyEndpointAutoScalingRuleAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    id: uuid.UUID
    modifier: EndpointAutoScalingRuleModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"


@dataclass
class DeleteEndpointAutoScalingRuleAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "delete"


@dataclass
class ScaleServiceReplicasAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    max_session_count_per_model_session: int
    service_id: uuid.UUID
    to: int

    @override
    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "scale"


@dataclass
class CreateEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointAutoScalingRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data is not None else None


@dataclass
class ModifyEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointAutoScalingRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.endpoint) if self.data is not None else None


@dataclass
class DeleteEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class ScaleServiceReplicasActionResult(BaseActionResult):
    current_route_count: int
    target_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
