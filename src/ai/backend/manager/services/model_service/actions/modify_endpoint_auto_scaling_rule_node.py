import uuid
from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.image.types import EndpointAutoScalingRuleData
from ai.backend.manager.services.model_service.actions.base import EndpointAction
from ai.backend.manager.services.model_service.types import RequesterCtx
from ai.backend.manager.types import OptionalState


@dataclass
class ModifyEndpointAutoScalingRuleAction(EndpointAction):
    requester_ctx: RequesterCtx
    id: uuid.UUID
    metric_source: OptionalState[AutoScalingMetricSource] = field(
        default_factory=lambda: OptionalState.nop("metric_source")
    )
    metric_name: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("metric_name")
    )
    threshold: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("threshold"))
    comparator: OptionalState[AutoScalingMetricComparator] = field(
        default_factory=lambda: OptionalState.nop("comparator")
    )
    step_size: OptionalState[int] = field(default_factory=lambda: OptionalState.nop("step_size"))
    cooldown_seconds: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("cooldown_seconds")
    )
    min_replicas: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("min_replicas")
    )
    max_replicas: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_replicas")
    )

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify-endpoint-auto-scaling-rule"


@dataclass
class ModifyEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointAutoScalingRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
