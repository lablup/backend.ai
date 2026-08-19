from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.services.model_serving.actions.create_auto_scaling_rule import (
    CreateEndpointAutoScalingRuleAction,
    CreateEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.actions.delete_auto_scaling_rule import (
    DeleteEndpointAutoScalingRuleAction,
    DeleteEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.actions.scale_service_replicas import (
    ScaleServiceReplicasAction,
    ScaleServiceReplicasActionResult,
)
from ai.backend.manager.services.model_serving.actions.update_auto_scaling_rule import (
    UpdateEndpointAutoScalingRuleAction,
    UpdateEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService


class ModelServingAutoScalingProcessors:
    scale_service_replicas: SingleEntityActionProcessor[
        ScaleServiceReplicasAction, ScaleServiceReplicasActionResult
    ]
    create_endpoint_auto_scaling_rule: SingleEntityActionProcessor[
        CreateEndpointAutoScalingRuleAction, CreateEndpointAutoScalingRuleActionResult
    ]
    delete_endpoint_auto_scaling_rule: SingleEntityActionProcessor[
        DeleteEndpointAutoScalingRuleAction, DeleteEndpointAutoScalingRuleActionResult
    ]
    update_endpoint_auto_scaling_rule: SingleEntityActionProcessor[
        UpdateEndpointAutoScalingRuleAction, UpdateEndpointAutoScalingRuleActionResult
    ]

    def __init__(
        self, group: ProcessorGroup[ModelDeploymentData], service: AutoScalingService
    ) -> None:
        self.scale_service_replicas = group.single_entity(
            ScaleServiceReplicasAction, service.scale_service_replicas
        )
        self.create_endpoint_auto_scaling_rule = group.single_entity(
            CreateEndpointAutoScalingRuleAction, service.create_endpoint_auto_scaling_rule
        )
        self.delete_endpoint_auto_scaling_rule = group.single_entity(
            DeleteEndpointAutoScalingRuleAction, service.delete_endpoint_auto_scaling_rule
        )
        self.update_endpoint_auto_scaling_rule = group.single_entity(
            UpdateEndpointAutoScalingRuleAction, service.update_endpoint_auto_scaling_rule
        )
