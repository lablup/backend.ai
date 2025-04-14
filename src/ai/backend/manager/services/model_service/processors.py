from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.model_service.actions.clear_error import (
    ClearErrorAction,
    ClearErrorActionResult,
)
from ai.backend.manager.services.model_service.actions.create_endpoint_auto_scaling_rule import (
    CreateEndpointAutoScalingRuleAction,
    CreateEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_service.actions.create_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_enpoint_auto_scaling_rule import (
    DeleteEndpointAutoScalingRuleAction,
    DeleteEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_route import (
    DeleteRouteAction,
    DeleteRouteActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_service import (
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.force_sync import (
    ForceSyncAction,
    ForceSyncActionResult,
)
from ai.backend.manager.services.model_service.actions.generate_token import (
    GenerateTokenAction,
    GenerateTokenActionResult,
)
from ai.backend.manager.services.model_service.actions.get_info import (
    GetModelServiceInfoAction,
    GetModelServiceInfoActionResult,
)
from ai.backend.manager.services.model_service.actions.list_errors import (
    ListErrorsAction,
    ListErrorsActionResult,
)
from ai.backend.manager.services.model_service.actions.list_service import (
    ListModelServiceAction,
    ListModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.modify_endpoint_auto_scaling_rule import (
    ModifyEndpointAutoScalingRuleAction,
    ModifyEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_service.actions.modify_enpoint import (
    ModifyEndpointAction,
    ModifyEndpointActionResult,
)
from ai.backend.manager.services.model_service.actions.scale import (
    ScaleServiceReplicasAction,
    ScaleServiceReplicasActionResult,
)
from ai.backend.manager.services.model_service.actions.start_service import (
    StartModelServiceAction,
    StartModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)
from ai.backend.manager.services.model_service.service import ModelService


class ModelServiceProcessors:
    create_model_service: ActionProcessor[CreateModelServiceAction, CreateModelServiceActionResult]
    list_model_service: ActionProcessor[ListModelServiceAction, ListModelServiceActionResult]
    delete_model_service: ActionProcessor[DeleteModelServiceAction, DeleteModelServiceActionResult]
    start_model_service: ActionProcessor[StartModelServiceAction, StartModelServiceActionResult]
    get_model_service_info: ActionProcessor[
        GetModelServiceInfoAction, GetModelServiceInfoActionResult
    ]
    list_errors: ActionProcessor[ListErrorsAction, ListErrorsActionResult]
    clear_error: ActionProcessor[ClearErrorAction, ClearErrorActionResult]
    scale_service_replicas: ActionProcessor[
        ScaleServiceReplicasAction, ScaleServiceReplicasActionResult
    ]
    force_sync: ActionProcessor[ForceSyncAction, ForceSyncActionResult]
    update_route: ActionProcessor[UpdateRouteAction, UpdateRouteActionResult]
    delete_route: ActionProcessor[DeleteRouteAction, DeleteRouteActionResult]
    generate_token: ActionProcessor[GenerateTokenAction, GenerateTokenActionResult]
    modify_endpoint: ActionProcessor[ModifyEndpointAction, ModifyEndpointActionResult]
    create_endpoint_auto_scaling_rule: ActionProcessor[
        CreateEndpointAutoScalingRuleAction, CreateEndpointAutoScalingRuleActionResult
    ]
    delete_endpoint_auto_scaling_rule: ActionProcessor[
        DeleteEndpointAutoScalingRuleAction, DeleteEndpointAutoScalingRuleActionResult
    ]
    modify_endpoint_auto_scaling_rule: ActionProcessor[
        ModifyEndpointAutoScalingRuleAction, ModifyEndpointAutoScalingRuleActionResult
    ]

    def __init__(self, service: ModelService) -> None:
        self.create_model_service = ActionProcessor(service.create)
        self.list_model_service = ActionProcessor(service.list_serve)
        self.delete_model_service = ActionProcessor(service.delete)
        self.start_model_service = ActionProcessor(service.try_start)
        self.get_model_service_info = ActionProcessor(service.get_model_service_info)
        self.list_errors = ActionProcessor(service.list_errors)
        self.clear_error = ActionProcessor(service.clear_error)
        self.scale_service_replicas = ActionProcessor(service.scale_service_replicas)
        self.force_sync = ActionProcessor(service.force_sync_with_app_proxy)
        self.update_route = ActionProcessor(service.update_route)
        self.delete_route = ActionProcessor(service.delete_route)
        self.generate_token = ActionProcessor(service.generate_token)
        self.modify_endpoint = ActionProcessor(service.modify_endpoint)
        self.create_endpoint_auto_scaling_rule = ActionProcessor(
            service.create_endpoint_auto_scaling_rule
        )
        self.delete_endpoint_auto_scaling_rule = ActionProcessor(
            service.delete_endpoint_auto_scaling_rule
        )
        self.modify_endpoint_auto_scaling_rule = ActionProcessor(
            service.modify_endpoint_auto_scaling_rule
        )
