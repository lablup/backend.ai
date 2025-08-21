from typing import Protocol, override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.model_serving.actions.clear_error import (
    ClearErrorAction,
    ClearErrorActionResult,
)
from ai.backend.manager.services.model_serving.actions.create_model_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.actions.delete_model_service import (
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.actions.delete_route import (
    DeleteRouteAction,
    DeleteRouteActionResult,
)
from ai.backend.manager.services.model_serving.actions.dry_run_model_service import (
    DryRunModelServiceAction,
    DryRunModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.actions.force_sync import (
    ForceSyncAction,
    ForceSyncActionResult,
)
from ai.backend.manager.services.model_serving.actions.generate_token import (
    GenerateTokenAction,
    GenerateTokenActionResult,
)
from ai.backend.manager.services.model_serving.actions.get_model_service_info import (
    GetModelServiceInfoAction,
    GetModelServiceInfoActionResult,
)
from ai.backend.manager.services.model_serving.actions.list_errors import (
    ListErrorsAction,
    ListErrorsActionResult,
)
from ai.backend.manager.services.model_serving.actions.list_model_service import (
    ListModelServiceAction,
    ListModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.actions.modify_endpoint import (
    ModifyEndpointAction,
    ModifyEndpointActionResult,
)
from ai.backend.manager.services.model_serving.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)


class ModelServingServiceProtocol(Protocol):
    """Protocol defining the interface for model serving services."""

    async def create(self, action: CreateModelServiceAction) -> CreateModelServiceActionResult: ...

    async def list_serve(self, action: ListModelServiceAction) -> ListModelServiceActionResult: ...

    async def delete(self, action: DeleteModelServiceAction) -> DeleteModelServiceActionResult: ...

    async def dry_run(self, action: DryRunModelServiceAction) -> DryRunModelServiceActionResult: ...

    async def get_model_service_info(
        self, action: GetModelServiceInfoAction
    ) -> GetModelServiceInfoActionResult: ...

    async def list_errors(self, action: ListErrorsAction) -> ListErrorsActionResult: ...

    async def clear_error(self, action: ClearErrorAction) -> ClearErrorActionResult: ...

    async def force_sync_with_app_proxy(self, action: ForceSyncAction) -> ForceSyncActionResult: ...

    async def update_route(self, action: UpdateRouteAction) -> UpdateRouteActionResult: ...

    async def delete_route(self, action: DeleteRouteAction) -> DeleteRouteActionResult: ...

    async def generate_token(self, action: GenerateTokenAction) -> GenerateTokenActionResult: ...

    async def modify_endpoint(self, action: ModifyEndpointAction) -> ModifyEndpointActionResult: ...


class ModelServingProcessors(AbstractProcessorPackage):
    create_model_service: ActionProcessor[CreateModelServiceAction, CreateModelServiceActionResult]
    list_model_service: ActionProcessor[ListModelServiceAction, ListModelServiceActionResult]
    delete_model_service: ActionProcessor[DeleteModelServiceAction, DeleteModelServiceActionResult]
    dry_run_model_service: ActionProcessor[DryRunModelServiceAction, DryRunModelServiceActionResult]
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

    def __init__(
        self,
        service: ModelServingServiceProtocol,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.create_model_service = ActionProcessor(service.create, action_monitors)
        self.list_model_service = ActionProcessor(service.list_serve, action_monitors)
        self.delete_model_service = ActionProcessor(service.delete, action_monitors)
        self.dry_run_model_service = ActionProcessor(service.dry_run, action_monitors)
        self.get_model_service_info = ActionProcessor(
            service.get_model_service_info, action_monitors
        )
        self.list_errors = ActionProcessor(service.list_errors, action_monitors)
        self.clear_error = ActionProcessor(service.clear_error, action_monitors)
        self.force_sync = ActionProcessor(service.force_sync_with_app_proxy, action_monitors)
        self.update_route = ActionProcessor(service.update_route, action_monitors)
        self.delete_route = ActionProcessor(service.delete_route, action_monitors)
        self.generate_token = ActionProcessor(service.generate_token, action_monitors)
        self.modify_endpoint = ActionProcessor(service.modify_endpoint, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateModelServiceAction.spec(),
            ListModelServiceAction.spec(),
            DeleteModelServiceAction.spec(),
            DryRunModelServiceAction.spec(),
            GetModelServiceInfoAction.spec(),
            ListErrorsAction.spec(),
            ClearErrorAction.spec(),
            ForceSyncAction.spec(),
            UpdateRouteAction.spec(),
            DeleteRouteAction.spec(),
            GenerateTokenAction.spec(),
            ModifyEndpointAction.spec(),
        ]
