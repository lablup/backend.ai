from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.model_service.actions.clear_error import (
    ClearErrorAction,
    ClearErrorActionResult,
)
from ai.backend.manager.services.model_service.actions.create_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_route import (
    DeleteRouteAction,
    DeleteRouteActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_service import (
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.generate_token import (
    GenerateTokenAction,
    GenerateTokenActionResult,
)
from ai.backend.manager.services.model_service.actions.get_info import (
    GetInfoAction,
    GetInfoActionResult,
)
from ai.backend.manager.services.model_service.actions.list_errors import (
    ListErrorsAction,
    ListErrorsActionResult,
)
from ai.backend.manager.services.model_service.actions.list_service import (
    ListModelServiceAction,
    ListModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.scale import ScaleAction, ScaleActionResult
from ai.backend.manager.services.model_service.actions.start_service import (
    StartModelServiceAction,
    StartModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.sync import SyncAction, SyncActionResult
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
    get_info: ActionProcessor[GetInfoAction, GetInfoActionResult]
    list_errors: ActionProcessor[ListErrorsAction, ListErrorsActionResult]
    clear_error: ActionProcessor[ClearErrorAction, ClearErrorActionResult]
    scale: ActionProcessor[ScaleAction, ScaleActionResult]
    sync: ActionProcessor[SyncAction, SyncActionResult]
    update_route: ActionProcessor[UpdateRouteAction, UpdateRouteActionResult]
    delete_route: ActionProcessor[DeleteRouteAction, DeleteRouteActionResult]
    generate_token: ActionProcessor[GenerateTokenAction, GenerateTokenActionResult]

    def __init__(self, service: ModelService) -> None:
        self.create_model_service = ActionProcessor(service.create)
        self.list_model_service = ActionProcessor(service.list_serve)
        self.delete_model_service = ActionProcessor(service.delete)
        self.start_model_service = ActionProcessor(service.try_start)
        self.get_info = ActionProcessor(service.get_info)
        self.list_errors = ActionProcessor(service.list_errors)
        self.clear_error = ActionProcessor(service.clear_error)
        self.scale = ActionProcessor(service.scale)
        self.sync = ActionProcessor(service.sync)
        self.update_route = ActionProcessor(service.update_route)
        self.delete_route = ActionProcessor(service.delete_route)
        self.generate_token = ActionProcessor(service.generate_token)
