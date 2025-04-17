from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.model_service.actions.base import (
    ClearErrorAction,
    ClearErrorActionResult,
    CreateModelServiceAction,
    CreateModelServiceActionResult,
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
    DeleteRouteAction,
    DeleteRouteActionResult,
    ForceSyncAction,
    ForceSyncActionResult,
    GenerateTokenAction,
    GenerateTokenActionResult,
    GetModelServiceInfoAction,
    GetModelServiceInfoActionResult,
    ListErrorsAction,
    ListErrorsActionResult,
    ListModelServiceAction,
    ListModelServiceActionResult,
    ModifyEndpointAction,
    ModifyEndpointActionResult,
    StartModelServiceAction,
    StartModelServiceActionResult,
    UpdateRouteAction,
    UpdateRouteActionResult,
)
from ai.backend.manager.services.model_service.services.model_service import ModelService


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
    force_sync: ActionProcessor[ForceSyncAction, ForceSyncActionResult]
    update_route: ActionProcessor[UpdateRouteAction, UpdateRouteActionResult]
    delete_route: ActionProcessor[DeleteRouteAction, DeleteRouteActionResult]
    generate_token: ActionProcessor[GenerateTokenAction, GenerateTokenActionResult]
    modify_endpoint: ActionProcessor[ModifyEndpointAction, ModifyEndpointActionResult]

    def __init__(self, service: ModelService) -> None:
        self.create_model_service = ActionProcessor(service.create)
        self.list_model_service = ActionProcessor(service.list_serve)
        self.delete_model_service = ActionProcessor(service.delete)
        self.start_model_service = ActionProcessor(service.try_start)
        self.get_model_service_info = ActionProcessor(service.get_model_service_info)
        self.list_errors = ActionProcessor(service.list_errors)
        self.clear_error = ActionProcessor(service.clear_error)
        self.force_sync = ActionProcessor(service.force_sync_with_app_proxy)
        self.update_route = ActionProcessor(service.update_route)
        self.delete_route = ActionProcessor(service.delete_route)
        self.generate_token = ActionProcessor(service.generate_token)
        self.modify_endpoint = ActionProcessor(service.modify_endpoint)
