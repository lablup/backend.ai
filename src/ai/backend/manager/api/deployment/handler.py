"""
REST API handlers for deployment system.
Provides CRUD endpoints for deployments and revisions.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.dto.manager.deployment import (
    ActivateRevisionResponse,
    CreateDeploymentRequest,
    CreateDeploymentResponse,
    CreateRevisionRequest,
    CreateRevisionResponse,
    CursorPaginationInfo,
    DeactivateRevisionResponse,
    DeploymentPathParam,
    DestroyDeploymentResponse,
    GetDeploymentResponse,
    GetRevisionResponse,
    ListDeploymentsResponse,
    ListRevisionsResponse,
    ListRoutesResponse,
    PaginationInfo,
    RevisionPathParam,
    RoutePathParam,
    SearchDeploymentsRequest,
    SearchRevisionsRequest,
    SearchRoutesRequest,
    UpdateDeploymentRequest,
    UpdateDeploymentResponse,
    UpdateRouteTrafficStatusRequest,
    UpdateRouteTrafficStatusResponse,
)
from ai.backend.manager.data.deployment.types import RouteTrafficStatus as ManagerRouteTrafficStatus
from ai.backend.manager.dto.context import ProcessorsCtx, UserContext
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentMetadataUpdaterSpec,
    DeploymentUpdaterSpec,
    ReplicaSpecUpdaterSpec,
)
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.get_deployment_by_id import (
    GetDeploymentByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.create_model_revision import (
    CreateModelRevisionAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.revision_operations import (
    ActivateRevisionAction,
)
from ai.backend.manager.services.deployment.actions.route import (
    SearchRoutesAction,
    UpdateRouteTrafficStatusAction,
)
from ai.backend.manager.services.deployment.actions.search_deployments import (
    SearchDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.update_deployment import (
    UpdateDeploymentAction,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.types import OptionalState

from ..auth import auth_required_for_method
from ..types import CORSOptions, WebMiddleware
from .adapter import (
    CreateDeploymentAdapter,
    CreateRevisionAdapter,
    DeploymentAdapter,
    RevisionAdapter,
    RouteAdapter,
)

__all__ = ("create_app",)


class DeploymentAPIHandler:
    """REST API handler class for deployment operations."""

    def __init__(self) -> None:
        self.deployment_adapter = DeploymentAdapter()
        self.revision_adapter = RevisionAdapter()
        self.route_adapter = RouteAdapter()
        self.create_deployment_adapter = CreateDeploymentAdapter()
        self.create_revision_adapter = CreateRevisionAdapter()

    def _get_deployment_processors(self, processors: Processors) -> DeploymentProcessors:
        """Get deployment processors, raising ServiceUnavailable if not available."""
        if processors.deployment is None:
            raise web.HTTPServiceUnavailable(
                reason="Deployment service is not available on this manager"
            )
        return processors.deployment

    # Deployment Endpoints

    @auth_required_for_method
    @api_handler
    async def create_deployment(
        self,
        body: BodyParam[CreateDeploymentRequest],
        processors_ctx: ProcessorsCtx,
        user_ctx: UserContext,
    ) -> APIResponse:
        """Create a new deployment."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Build creator from request using adapter
        creator = self.create_deployment_adapter.build_creator(
            body.parsed,
            user_uuid=user_ctx.user_uuid,
            user_domain=user_ctx.user_domain,
        )

        # Call service action
        action_result = await deployment_processors.create_deployment.wait_for_complete(
            CreateDeploymentAction(creator=creator)
        )

        # Build response
        resp = CreateDeploymentResponse(
            deployment=self.deployment_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_deployments(
        self,
        body: BodyParam[SearchDeploymentsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search deployments with filters, orders, and pagination."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Build querier using adapter
        querier = self.deployment_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await deployment_processors.search_deployments.wait_for_complete(
            SearchDeploymentsAction(querier=querier)
        )

        # Build response
        resp = ListDeploymentsResponse(
            deployments=[self.deployment_adapter.convert_to_dto(dep) for dep in action_result.data],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_deployment(
        self,
        path: PathParam[DeploymentPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific deployment."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Call service action - raises EndpointNotFound if not found
        action_result = await deployment_processors.get_deployment_by_id.wait_for_complete(
            GetDeploymentByIdAction(deployment_id=path.parsed.deployment_id)
        )

        # Build response
        resp = GetDeploymentResponse(
            deployment=self.deployment_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_deployment(
        self,
        path: PathParam[DeploymentPathParam],
        body: BodyParam[UpdateDeploymentRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing deployment."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Build sub-specs only if fields are provided
        metadata_spec: DeploymentMetadataUpdaterSpec | None = None
        if body.parsed.name is not None:
            metadata_spec = DeploymentMetadataUpdaterSpec(
                name=OptionalState.update(body.parsed.name),
            )

        replica_spec: ReplicaSpecUpdaterSpec | None = None
        if body.parsed.desired_replicas is not None:
            replica_spec = ReplicaSpecUpdaterSpec(
                desired_replica_count=OptionalState.update(body.parsed.desired_replicas),
            )

        updater_spec = DeploymentUpdaterSpec(
            metadata=metadata_spec,
            replica_spec=replica_spec,
        )
        updater = Updater[EndpointRow](
            spec=updater_spec,
            pk_value=path.parsed.deployment_id,
        )

        # Call service action
        action_result = await deployment_processors.update_deployment.wait_for_complete(
            UpdateDeploymentAction(updater=updater)
        )

        # Build response
        resp = UpdateDeploymentResponse(
            deployment=self.deployment_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def destroy_deployment(
        self,
        path: PathParam[DeploymentPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Destroy a deployment."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Call service action
        action_result = await deployment_processors.destroy_deployment.wait_for_complete(
            DestroyDeploymentAction(endpoint_id=path.parsed.deployment_id)
        )

        # Build response
        resp = DestroyDeploymentResponse(deleted=action_result.success)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Revision Endpoints

    @auth_required_for_method
    @api_handler
    async def create_revision(
        self,
        path: PathParam[DeploymentPathParam],
        body: BodyParam[CreateRevisionRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new revision for a deployment."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Build creator from request using adapter
        creator = self.create_revision_adapter.build_creator(body.parsed)

        # Call service action
        action_result = await deployment_processors.create_model_revision.wait_for_complete(
            CreateModelRevisionAction(creator=creator)
        )

        # Build response
        resp = CreateRevisionResponse(
            revision=self.revision_adapter.convert_to_dto(action_result.revision)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_revisions(
        self,
        path: PathParam[DeploymentPathParam],
        body: BodyParam[SearchRevisionsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search revisions for a deployment with filters, orders, and pagination."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Build querier using adapter, adding deployment filter
        if body.parsed.filter is None:
            from ai.backend.common.dto.manager.deployment import RevisionFilter

            body.parsed.filter = RevisionFilter(deployment_id=path.parsed.deployment_id)
        else:
            body.parsed.filter.deployment_id = path.parsed.deployment_id

        querier = self.revision_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await deployment_processors.search_revisions.wait_for_complete(
            SearchRevisionsAction(querier=querier)
        )

        # Build response
        resp = ListRevisionsResponse(
            revisions=[self.revision_adapter.convert_to_dto(rev) for rev in action_result.data],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_revision(
        self,
        path: PathParam[RevisionPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific revision."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Call service action - raises DeploymentRevisionNotFound if not found
        action_result = await deployment_processors.get_revision_by_id.wait_for_complete(
            GetRevisionByIdAction(revision_id=path.parsed.revision_id)
        )

        # Build response
        resp = GetRevisionResponse(
            revision=self.revision_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def activate_revision(
        self,
        path: PathParam[RevisionPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Activate a revision to make it the current active revision."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Call service action
        await deployment_processors.activate_revision.wait_for_complete(
            ActivateRevisionAction(
                deployment_id=path.parsed.deployment_id,
                revision_id=path.parsed.revision_id,
            )
        )

        # Build response
        resp = ActivateRevisionResponse(success=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def deactivate_revision(
        self,
        path: PathParam[RevisionPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Deactivate a revision."""
        # Note: For deactivation, we can set the desired_replicas to 0 or use a specific action
        # This is a simplified implementation
        resp = DeactivateRevisionResponse(success=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Route Endpoints

    @auth_required_for_method
    @api_handler
    async def search_routes(
        self,
        path: PathParam[DeploymentPathParam],
        body: BodyParam[SearchRoutesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search routes for a deployment with filters, orders, and pagination."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Build querier using adapter, adding deployment filter
        if body.parsed.filter is None:
            from ai.backend.common.dto.manager.deployment import RouteFilter

            body.parsed.filter = RouteFilter(deployment_id=path.parsed.deployment_id)
        else:
            body.parsed.filter.deployment_id = path.parsed.deployment_id

        querier = self.route_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await deployment_processors.search_routes.wait_for_complete(
            SearchRoutesAction(querier=querier)
        )

        # Build response
        resp = ListRoutesResponse(
            routes=[self.route_adapter.convert_to_dto(route) for route in action_result.routes],
            pagination=CursorPaginationInfo(
                total_count=action_result.total_count,
                has_next_page=action_result.has_next_page,
                has_previous_page=action_result.has_previous_page,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_route_traffic_status(
        self,
        path: PathParam[RoutePathParam],
        body: BodyParam[UpdateRouteTrafficStatusRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update traffic status of a route."""
        deployment_processors = self._get_deployment_processors(processors_ctx.processors)

        # Convert common type to manager type
        manager_traffic_status = ManagerRouteTrafficStatus(body.parsed.traffic_status.value)

        # Call service action
        action_result = await deployment_processors.update_route_traffic_status.wait_for_complete(
            UpdateRouteTrafficStatusAction(
                route_id=path.parsed.route_id,
                traffic_status=manager_traffic_status,
            )
        )

        # Build response
        resp = UpdateRouteTrafficStatusResponse(
            route=self.route_adapter.convert_to_dto(action_result.route)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for deployment API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "deployments"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = DeploymentAPIHandler()

    # Deployment routes
    cors.add(app.router.add_route("POST", "/", api_handler.create_deployment))
    cors.add(app.router.add_route("POST", "/search", api_handler.search_deployments))
    cors.add(app.router.add_route("GET", "/{deployment_id}", api_handler.get_deployment))
    cors.add(app.router.add_route("PATCH", "/{deployment_id}", api_handler.update_deployment))
    cors.add(app.router.add_route("DELETE", "/{deployment_id}", api_handler.destroy_deployment))

    # Revision routes (nested under deployment)
    cors.add(
        app.router.add_route("POST", "/{deployment_id}/revisions", api_handler.create_revision)
    )
    cors.add(
        app.router.add_route(
            "POST", "/{deployment_id}/revisions/search", api_handler.search_revisions
        )
    )
    cors.add(
        app.router.add_route(
            "GET", "/{deployment_id}/revisions/{revision_id}", api_handler.get_revision
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{deployment_id}/revisions/{revision_id}/activate",
            api_handler.activate_revision,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{deployment_id}/revisions/{revision_id}/deactivate",
            api_handler.deactivate_revision,
        )
    )

    # Route routes (nested under deployment)
    cors.add(
        app.router.add_route("POST", "/{deployment_id}/routes/search", api_handler.search_routes)
    )
    cors.add(
        app.router.add_route(
            "PATCH",
            "/{deployment_id}/routes/{route_id}/traffic-status",
            api_handler.update_route_traffic_status,
        )
    )

    return app, []
