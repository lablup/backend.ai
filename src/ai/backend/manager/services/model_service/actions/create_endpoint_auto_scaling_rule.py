import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import EndpointAction
from ai.backend.manager.services.model_service.types import (
    EndpointAutoScalingRuleData,
    RequesterCtx,
)


@dataclass
class CreateEndpointAutoScalingRuleAction(EndpointAction):
    requester_ctx: RequesterCtx
    endpoint_id: uuid.UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: str
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: Optional[int]
    max_replicas: Optional[int]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def entity_type(self) -> str:
        return "endpoint"


@dataclass
class CreateEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointAutoScalingRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
