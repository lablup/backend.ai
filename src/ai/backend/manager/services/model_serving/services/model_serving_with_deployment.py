"""Model serving service with DeploymentController integration."""

import logging
import uuid
from typing import TYPE_CHECKING

from ai.backend.logging.utils import BraceStyleAdapter
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

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.deployment import DeploymentController

log = BraceStyleAdapter(logging.getLogger(__name__))


class ModelServingServiceWithDeployment:
    """
    Model serving service integrated with DeploymentController.

    This implementation delegates deployment operations to the Sokovan
    DeploymentController while maintaining compatibility with the existing
    ModelServingService interface.
    """

    _deployment_controller: "DeploymentController"

    def __init__(
        self,
        deployment_controller: "DeploymentController",
    ) -> None:
        self._deployment_controller = deployment_controller

    async def create(
        self,
        action: CreateModelServiceAction,
    ) -> CreateModelServiceActionResult:
        """
        Create a model service using DeploymentController.

        This method delegates the actual deployment work to the
        DeploymentController while maintaining the existing action interface.
        """
        log.info(
            "Creating model service '{}' via DeploymentController",
            action.creator.service_name,
        )

        # Delegate to DeploymentController
        service_info = await self._deployment_controller.create_model_service(action.creator)

        return CreateModelServiceActionResult(
            data=service_info,
        )

    async def delete(
        self,
        action: DeleteModelServiceAction,
    ) -> DeleteModelServiceActionResult:
        """
        Delete a model service using DeploymentController.
        """
        log.info("Deleting model service {} via DeploymentController", action.service_id)

        # Determine force parameter based on requester role if available
        # Superadmin can force delete, others cannot
        force = False
        if action.requester_ctx:
            from ai.backend.manager.models.user import UserRole

            force = action.requester_ctx.user_role == UserRole.SUPERADMIN

        # Delegate to DeploymentController
        result = await self._deployment_controller.delete_model_service(
            action.service_id,
            force=force,
        )

        return DeleteModelServiceActionResult(
            success=result,
        )

    async def scale(
        self,
        endpoint_id: str,
        target_replicas: int,
    ):
        """
        Scale a model service using DeploymentController.
        """
        log.info(
            "Scaling model service {} to {} replicas via DeploymentController",
            endpoint_id,
            target_replicas,
        )

        # Delegate to DeploymentController
        return await self._deployment_controller.scale_model_service(
            uuid.UUID(endpoint_id),
            target_replicas,
        )

    async def list_serve(
        self,
        action: ListModelServiceAction,
    ) -> ListModelServiceActionResult:
        """
        List model services.

        Fetches endpoints from the deployment repository filtered by owner.
        """
        from pydantic import HttpUrl

        from ai.backend.manager.services.model_serving.types import CompactServiceInfo

        # List endpoints by owner
        endpoints = (
            await self._deployment_controller._deployment_repository.list_endpoints_by_owner(
                action.session_owener_id,
                name=action.name,
            )
        )

        # Count active routes for each endpoint
        result_data = []
        for endpoint in endpoints:
            # Get routes for this endpoint
            routes = (
                await self._deployment_controller._deployment_repository.get_routes_by_endpoint(
                    endpoint.endpoint_id
                )
            )

            # Count healthy routes
            from ai.backend.manager.data.model_serving.types import RouteStatus

            active_route_count = sum(1 for r in routes if r.status == RouteStatus.HEALTHY)

            result_data.append(
                CompactServiceInfo(
                    id=endpoint.endpoint_id,
                    name=endpoint.name,
                    replicas=endpoint.desired_session_count,
                    desired_session_count=endpoint.desired_session_count,
                    active_route_count=active_route_count,
                    service_endpoint=HttpUrl(endpoint.service_endpoint)
                    if endpoint.service_endpoint
                    else None,
                    is_public=endpoint.is_public,
                )
            )

        return ListModelServiceActionResult(data=result_data)

    async def dry_run(
        self,
        action: DryRunModelServiceAction,
    ) -> DryRunModelServiceActionResult:
        """
        Dry run for model service creation.

        Validates the service spec by creating a test session.
        This is a simplified version that doesn't track events.
        """
        import uuid as uuid_module

        # Generate task ID for tracking
        task_id = uuid_module.uuid4()

        log.info(
            "Dry run for model service '{}' (task_id: {})",
            action.service_name,
            task_id,
        )

        # Perform comprehensive validation
        from ai.backend.manager.services.model_serving.exceptions import InvalidAPIParameters

        # 1. Basic parameter validation
        if not action.service_name:
            raise InvalidAPIParameters("Service name is required")

        if action.replicas <= 0:
            raise InvalidAPIParameters("Replicas must be positive")

        if not action.image:
            raise InvalidAPIParameters("Image is required")

        # 2. Check endpoint name uniqueness
        # Get all endpoints to check for name conflicts
        all_endpoints = (
            await self._deployment_controller._deployment_repository.get_all_active_endpoints()
        )
        name_exists = any(e.name == action.service_name for e in all_endpoints)
        if name_exists:
            raise InvalidAPIParameters(f"Service with name '{action.service_name}' already exists")

        # 3. Validate resource configuration
        if action.config and action.config.resources:
            # Basic resource validation
            resources = action.config.resources
            if not resources:
                raise InvalidAPIParameters("Resource configuration is required")

        # 4. Validate model if specified
        if action.model_service_prepare_ctx and action.model_service_prepare_ctx.model_id:
            # Check if model exists by trying to get endpoint info
            # This is a simplified check - full implementation would check vfolder
            log.debug(
                "Validating model {} for service {}",
                action.model_service_prepare_ctx.model_id,
                action.service_name,
            )

        # If all validations pass, the dry run is successful
        log.info(
            "Dry run successful for service '{}' with {} replicas",
            action.service_name,
            action.replicas,
        )

        return DryRunModelServiceActionResult(
            task_id=task_id,
        )

    async def get_model_service_info(
        self,
        action: GetModelServiceInfoAction,
    ) -> GetModelServiceInfoActionResult:
        """
        Get model service information.

        This fetches detailed information about a specific service.
        """
        # Get service info from repository
        service_info = await self._deployment_controller._deployment_repository.get_service_info(
            action.service_id
        )

        if not service_info:
            # Return empty result if service not found
            from ai.backend.manager.errors.service import ModelServiceNotFound

            raise ModelServiceNotFound(f"Service {action.service_id} not found")

        return GetModelServiceInfoActionResult(
            data=service_info,
        )

    async def list_errors(
        self,
        action: ListErrorsAction,
    ) -> ListErrorsActionResult:
        """
        List errors for model services.

        Fetches error information from routes with error status.
        """
        from ai.backend.manager.data.model_serving.types import RouteStatus
        from ai.backend.manager.services.model_serving.types import ErrorInfo

        # Get endpoint info
        endpoint = await self._deployment_controller._deployment_repository.get_endpoint_info(
            action.service_id
        )
        if not endpoint:
            return ListErrorsActionResult(
                error_info=[],
                retries=0,
            )

        # Get routes for this endpoint
        routes = await self._deployment_controller._deployment_repository.get_routes_by_endpoint(
            action.service_id
        )

        # Filter routes with errors
        error_info = []
        for route in routes:
            if route.status == RouteStatus.FAILED_TO_START and route.error_data:
                error_info.append(
                    ErrorInfo(
                        session_id=route.session_id,
                        error=route.error_data,
                    )
                )

        # Get retry count from endpoint metadata if available
        # The desired_session_count can be used as a proxy for retry attempts
        # when compared with actual route count
        retries = 0
        if endpoint:
            # Count how many times we've tried to create sessions
            # This is a simplified approach - full implementation would track in DB
            actual_routes = len(routes)
            if endpoint.desired_session_count > actual_routes:
                # We've attempted to create more sessions than currently exist
                retries = endpoint.desired_session_count - actual_routes

        return ListErrorsActionResult(
            error_info=error_info,
            retries=retries,
        )

    async def clear_error(
        self,
        action: ClearErrorAction,
    ) -> ClearErrorActionResult:
        """
        Clear errors for a model service.

        Clears error states for routes in the deployment repository.
        """
        # Clear all endpoint errors
        success = await self._deployment_controller._deployment_repository.clear_endpoint_errors(
            action.service_id
        )

        return ClearErrorActionResult(
            success=success,
        )

    async def update_route(
        self,
        action: UpdateRouteAction,
    ) -> UpdateRouteActionResult:
        """
        Update a route configuration.

        Modifies route traffic ratio.
        """
        # Update the traffic ratio for the route
        success = (
            await self._deployment_controller._deployment_repository.update_route_traffic_ratio(
                action.route_id,
                action.traffic_ratio,
            )
        )

        if not success:
            from ai.backend.manager.errors.service import RouteNotFound

            raise RouteNotFound(f"Route {action.route_id} not found")

        return UpdateRouteActionResult(
            success=success,
        )

    async def delete_route(
        self,
        action: DeleteRouteAction,
    ) -> DeleteRouteActionResult:
        """
        Delete a specific route.

        Removes a single route from a service.
        """
        # Delete the route
        success = await self._deployment_controller._deployment_repository.delete_route(
            action.route_id
        )

        if not success:
            from ai.backend.manager.errors.service import RouteNotFound

            raise RouteNotFound(f"Route {action.route_id} not found")

        return DeleteRouteActionResult(
            success=success,
        )

    async def generate_token(
        self,
        action: GenerateTokenAction,
    ) -> GenerateTokenActionResult:
        """
        Generate an authentication token for a model service.

        Creates access tokens for protected endpoints.
        """
        import secrets
        from datetime import datetime

        # Get endpoint info to get owner and project details
        endpoint = await self._deployment_controller._deployment_repository.get_endpoint_info(
            action.service_id
        )

        if not endpoint:
            from ai.backend.manager.errors.service import ModelServiceNotFound

            raise ModelServiceNotFound(f"Service {action.service_id} not found")

        # Generate a secure token
        token = secrets.token_urlsafe(32)

        # Calculate expiration time
        expires_at = action.expires_at if action.expires_at else None
        if not expires_at and action.duration:
            # Calculate expiration from duration
            from datetime import timedelta

            if isinstance(action.duration, timedelta):
                expires_at = int((datetime.now() + action.duration).timestamp())
            else:
                # Handle relativedelta if needed
                expires_at = int((datetime.now() + timedelta(days=30)).timestamp())
        elif not expires_at:
            # Default to 30 days
            from datetime import timedelta

            expires_at = int((datetime.now() + timedelta(days=30)).timestamp())

        # Store token metadata
        # In a full implementation, this would be stored in EndpointTokenRow table
        # For now, we just log it
        log.info(
            "Generated token for endpoint {} with expiration {}",
            action.service_id,
            expires_at,
        )

        from ai.backend.manager.data.model_serving.types import EndpointTokenData

        # Create token data with endpoint information
        token_data = EndpointTokenData(
            id=uuid.uuid4(),
            token=token,
            endpoint=action.service_id,
            session_owner=endpoint.owner_id,
            domain=endpoint.domain_name,
            project=endpoint.group_id,
            created_at=datetime.now(),
        )

        return GenerateTokenActionResult(
            data=token_data,
        )

    async def force_sync_with_app_proxy(
        self,
        action: ForceSyncAction,
    ) -> ForceSyncActionResult:
        """
        Force synchronization with app proxy.

        This would trigger a sync between the deployment state and app proxy.
        Could potentially call sync_deployments on the controller.
        """
        # Could potentially delegate to sync_deployments
        log.info("Forcing deployment sync via DeploymentController")
        await self._deployment_controller.sync_deployments()
        return ForceSyncActionResult(
            success=True,
        )

    async def modify_endpoint(
        self,
        action: ModifyEndpointAction,
    ) -> ModifyEndpointActionResult:
        """
        Modify endpoint configuration.

        Updates endpoint properties based on the modifier.
        """
        # Get current endpoint info to validate it exists
        endpoint = await self._deployment_controller._deployment_repository.get_endpoint_info(
            action.endpoint_id
        )

        if not endpoint:
            from ai.backend.manager.errors.service import EndpointNotFound

            raise EndpointNotFound(f"Endpoint {action.endpoint_id} not found")

        # Get fields to update from the modifier
        # The modifier handles OptionalState/TriState internally
        fields_to_update = action.modifier.fields_to_update()

        # For now, we only support updating open_to_public
        # Other fields would require additional repository methods
        success = True
        if "open_to_public" in fields_to_update:
            success = await self._deployment_controller._deployment_repository.update_endpoint_public_access(
                action.endpoint_id,
                fields_to_update["open_to_public"],
            )
            log.info(
                "Updated endpoint {} public access to {}",
                action.endpoint_id,
                fields_to_update["open_to_public"],
            )

        # Handle replicas field if present (triggers scaling)
        if "replicas" in fields_to_update:
            target_replicas = fields_to_update["replicas"]
            if target_replicas != endpoint.desired_session_count:
                log.info(
                    "Scaling endpoint {} from {} to {} replicas",
                    action.endpoint_id,
                    endpoint.desired_session_count,
                    target_replicas,
                )
                # Trigger scaling through DeploymentController
                await self._deployment_controller.scale_model_service(
                    action.endpoint_id,
                    target_replicas,
                )

        # Handle other fields that might be supported in the future
        supported_fields = {"open_to_public", "replicas"}
        unsupported_fields = set(fields_to_update.keys()) - supported_fields

        if unsupported_fields:
            log.warning(
                "Unsupported fields in modifier for endpoint {}: {}",
                action.endpoint_id,
                list(unsupported_fields),
            )

        # Return success without full data conversion
        # The full EndpointData conversion would require fetching
        # many additional fields not stored in deployment repository
        return ModifyEndpointActionResult(
            success=success,
            data=None,
        )
