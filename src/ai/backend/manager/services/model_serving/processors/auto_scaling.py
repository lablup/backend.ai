from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.model_serving.actions.create_auto_scaling_rule import (
    CreateEndpointAutoScalingRuleAction,
    CreateEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.actions.delete_auto_scaling_rule import (
    DeleteEndpointAutoScalingRuleAction,
    DeleteEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.actions.modify_auto_scaling_rule import (
    ModifyEndpointAutoScalingRuleAction,
    ModifyEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.actions.scale_service_replicas import (
    ScaleServiceReplicasAction,
    ScaleServiceReplicasActionResult,
)
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService


class ModelServingAutoScalingProcessors(AbstractProcessorPackage):
    scale_service_replicas: ActionProcessor[
        ScaleServiceReplicasAction, ScaleServiceReplicasActionResult
    ]
    create_endpoint_auto_scaling_rule: ActionProcessor[
        CreateEndpointAutoScalingRuleAction, CreateEndpointAutoScalingRuleActionResult
    ]
    delete_endpoint_auto_scaling_rule: ActionProcessor[
        DeleteEndpointAutoScalingRuleAction, DeleteEndpointAutoScalingRuleActionResult
    ]
    modify_endpoint_auto_scaling_rule: ActionProcessor[
        ModifyEndpointAutoScalingRuleAction, ModifyEndpointAutoScalingRuleActionResult
    ]

    def __init__(self, service: AutoScalingService, action_monitors: list[ActionMonitor]) -> None:
        self.scale_service_replicas = ActionProcessor(
            service.scale_service_replicas, action_monitors
        )
        self.create_endpoint_auto_scaling_rule = ActionProcessor(
            service.create_endpoint_auto_scaling_rule, action_monitors
        )
        self.delete_endpoint_auto_scaling_rule = ActionProcessor(
            service.delete_endpoint_auto_scaling_rule, action_monitors
        )
        self.modify_endpoint_auto_scaling_rule = ActionProcessor(
            service.modify_endpoint_auto_scaling_rule, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ScaleServiceReplicasAction.spec(),
            CreateEndpointAutoScalingRuleAction.spec(),
            DeleteEndpointAutoScalingRuleAction.spec(),
            ModifyEndpointAutoScalingRuleAction.spec(),
        ]
