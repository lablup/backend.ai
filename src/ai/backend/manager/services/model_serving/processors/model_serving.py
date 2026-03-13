from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
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
from ai.backend.manager.services.model_serving.actions.search_services import (
    SearchServicesAction,
    SearchServicesActionResult,
)
from ai.backend.manager.services.model_serving.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)
from ai.backend.manager.services.model_serving.actions.validate_model_service import (
    ValidateModelServiceAction,
    ValidateModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.services.model_serving import (
    ModelServingService,
)


class ModelServingProcessors(AbstractProcessorPackage):
    # Scope actions (with RBAC)
    create_model_service: ScopeActionProcessor[
        CreateModelServiceAction, CreateModelServiceActionResult
    ]
    list_model_service: ScopeActionProcessor[ListModelServiceAction, ListModelServiceActionResult]
    search_services: ActionProcessor[SearchServicesAction, SearchServicesActionResult]

    # Single entity actions (with RBAC)
    get_model_service_info: SingleEntityActionProcessor[
        GetModelServiceInfoAction, GetModelServiceInfoActionResult
    ]
    delete_model_service: SingleEntityActionProcessor[
        DeleteModelServiceAction, DeleteModelServiceActionResult
    ]
    modify_endpoint: SingleEntityActionProcessor[ModifyEndpointAction, ModifyEndpointActionResult]
    update_route: SingleEntityActionProcessor[UpdateRouteAction, UpdateRouteActionResult]
    delete_route: SingleEntityActionProcessor[DeleteRouteAction, DeleteRouteActionResult]

    # Internal/system actions (no RBAC)
    dry_run_model_service: ActionProcessor[DryRunModelServiceAction, DryRunModelServiceActionResult]
    list_errors: ActionProcessor[ListErrorsAction, ListErrorsActionResult]
    clear_error: ActionProcessor[ClearErrorAction, ClearErrorActionResult]
    force_sync: ActionProcessor[ForceSyncAction, ForceSyncActionResult]
    generate_token: ActionProcessor[GenerateTokenAction, GenerateTokenActionResult]
    validate_model_service: ActionProcessor[
        ValidateModelServiceAction, ValidateModelServiceActionResult
    ]

    def __init__(
        self,
        service: ModelServingService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Scope actions with RBAC validator
        self.create_model_service = ScopeActionProcessor(
            service.create, action_monitors, validators=[validators.rbac.scope]
        )
        self.list_model_service = ScopeActionProcessor(
            service.list_serve, action_monitors, validators=[validators.rbac.scope]
        )
        self.search_services = ActionProcessor(service.search_services, action_monitors)

        # Single entity actions with RBAC validator
        self.get_model_service_info = SingleEntityActionProcessor(
            service.get_model_service_info,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.delete_model_service = SingleEntityActionProcessor(
            service.delete, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.modify_endpoint = SingleEntityActionProcessor(
            service.modify_endpoint, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.update_route = SingleEntityActionProcessor(
            service.update_route, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.delete_route = SingleEntityActionProcessor(
            service.delete_route, action_monitors, validators=[validators.rbac.single_entity]
        )

        # Internal/system actions without RBAC
        self.dry_run_model_service = ActionProcessor(service.dry_run, action_monitors)
        self.list_errors = ActionProcessor(service.list_errors, action_monitors)
        self.clear_error = ActionProcessor(service.clear_error, action_monitors)
        self.force_sync = ActionProcessor(service.force_sync_with_app_proxy, action_monitors)
        self.generate_token = ActionProcessor(service.generate_token, action_monitors)
        self.validate_model_service = ActionProcessor(
            service.validate_model_service, action_monitors
        )

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
            SearchServicesAction.spec(),
            ValidateModelServiceAction.spec(),
        ]
