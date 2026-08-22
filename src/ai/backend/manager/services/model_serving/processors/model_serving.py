from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.services.model_serving.actions.clear_error import (
    ClearErrorAction,
    ClearErrorActionResult,
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
from ai.backend.manager.services.model_serving.actions.search_services import (
    SearchServicesAction,
    SearchServicesActionResult,
)
from ai.backend.manager.services.model_serving.actions.update_endpoint import (
    UpdateEndpointAction,
    UpdateEndpointActionResult,
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


class ModelServingProcessors:
    list_model_service: ScopeActionProcessor[ListModelServiceAction, ListModelServiceActionResult]
    search_services: ScopeActionProcessor[SearchServicesAction, SearchServicesActionResult]

    # Single entity actions (with RBAC)
    get_model_service_info: SingleEntityActionProcessor[
        GetModelServiceInfoAction, GetModelServiceInfoActionResult
    ]
    delete_model_service: SingleEntityActionProcessor[
        DeleteModelServiceAction, DeleteModelServiceActionResult
    ]
    update_endpoint: SingleEntityActionProcessor[UpdateEndpointAction, UpdateEndpointActionResult]
    update_route: SingleEntityActionProcessor[UpdateRouteAction, UpdateRouteActionResult]
    delete_route: SingleEntityActionProcessor[DeleteRouteAction, DeleteRouteActionResult]

    # Internal/system actions (no RBAC)
    dry_run_model_service: ScopeActionProcessor[
        DryRunModelServiceAction, DryRunModelServiceActionResult
    ]
    list_errors: SingleEntityActionProcessor[ListErrorsAction, ListErrorsActionResult]
    clear_error: SingleEntityActionProcessor[ClearErrorAction, ClearErrorActionResult]
    force_sync: SingleEntityActionProcessor[ForceSyncAction, ForceSyncActionResult]
    generate_token: SingleEntityActionProcessor[GenerateTokenAction, GenerateTokenActionResult]
    validate_model_service: ScopeActionProcessor[
        ValidateModelServiceAction, ValidateModelServiceActionResult
    ]

    def __init__(
        self, group: ProcessorGroup[ModelDeploymentData], service: ModelServingService
    ) -> None:
        self.list_model_service = group.scope(ListModelServiceAction, service.list_serve)
        self.search_services = group.scope(SearchServicesAction, service.search_services)

        # Single entity actions with RBAC validator
        self.get_model_service_info = group.single_entity(
            GetModelServiceInfoAction, service.get_model_service_info
        )
        self.delete_model_service = group.single_entity(DeleteModelServiceAction, service.delete)
        self.update_endpoint = group.single_entity(UpdateEndpointAction, service.update_endpoint)
        self.update_route = group.single_entity(UpdateRouteAction, service.update_route)
        self.delete_route = group.single_entity(DeleteRouteAction, service.delete_route)

        # Internal/system actions without RBAC
        self.dry_run_model_service = group.scope(DryRunModelServiceAction, service.dry_run)
        self.list_errors = group.single_entity(ListErrorsAction, service.list_errors)
        self.clear_error = group.single_entity(ClearErrorAction, service.clear_error)
        self.force_sync = group.single_entity(ForceSyncAction, service.force_sync_with_app_proxy)
        self.generate_token = group.single_entity(GenerateTokenAction, service.generate_token)
        self.validate_model_service = group.scope(
            ValidateModelServiceAction, service.validate_model_service
        )
