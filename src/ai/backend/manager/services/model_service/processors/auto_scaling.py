from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.model_service.actions.create_auto_scaling_rule import (
    CreateEndpointAutoScalingRuleAction,
    CreateEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_auto_scaling_rule import (
    DeleteEndpointAutoScalingRuleAction,
    DeleteEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_service.actions.modify_auto_scaling_rule import (
    ModifyEndpointAutoScalingRuleAction,
    ModifyEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_service.actions.scale_service_replicas import (
    ScaleServiceReplicasAction,
    ScaleServiceReplicasActionResult,
)
from ai.backend.manager.services.model_service.services.auto_scaling import AutoScalingService


class ModelServiceAutoScalingProcessors:
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
