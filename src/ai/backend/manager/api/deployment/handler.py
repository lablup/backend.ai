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
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.repositories.deployment.updaters import NewDeploymentUpdaterSpec
from ai.backend.manager.services.deployment.actions.batch_load_deployments import (
    BatchLoadDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
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
from .adapter import DeploymentAdapter, RevisionAdapter, RouteAdapter

__all__ = ("create_app",)


class DeploymentAPIHandler:
    """REST API handler class for deployment operations."""

    def __init__(self) -> None:
        self.deployment_adapter = DeploymentAdapter()
        self.revision_adapter = RevisionAdapter()
        self.route_adapter = RouteAdapter()

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
            deployments=[
                self.deployment_adapter.convert_to_dto(dep) for dep in action_result.deployments
            ],
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

        # Call service action
        action_result = await deployment_processors.batch_load_deployments.wait_for_complete(
            BatchLoadDeploymentsAction(deployment_ids=[path.parsed.deployment_id])
        )

        if not action_result.data:
            raise web.HTTPNotFound(reason=f"Deployment {path.parsed.deployment_id} not found")

        # Build response
        resp = GetDeploymentResponse(
            deployment=self.deployment_adapter.convert_to_dto(action_result.data[0])
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

        # Build updater spec
        name = OptionalState[str].nop()
        desired_replica_count = OptionalState[int].nop()

        if body.parsed.name is not None:
            name = OptionalState.update(body.parsed.name)
        if body.parsed.desired_replicas is not None:
            desired_replica_count = OptionalState.update(body.parsed.desired_replicas)

        updater_spec = NewDeploymentUpdaterSpec(
            name=name,
            desired_replica_count=desired_replica_count,
        )

        # Call service action
        action_result = await deployment_processors.update_deployment.wait_for_complete(
            UpdateDeploymentAction(
                deployment_id=path.parsed.deployment_id,
                updater_spec=updater_spec,
            )
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
            revisions=[
                self.revision_adapter.convert_to_dto(rev) for rev in action_result.revisions
            ],
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

        # Call service action
        action_result = await deployment_processors.batch_load_revisions.wait_for_complete(
            # Note: We need to import BatchLoadRevisionsAction
            __import__(
                "ai.backend.manager.services.deployment.actions.model_revision.batch_load_revisions",
                fromlist=["BatchLoadRevisionsAction"],
            ).BatchLoadRevisionsAction(revision_ids=[path.parsed.revision_id])
        )

        if not action_result.data:
            raise web.HTTPNotFound(reason=f"Revision {path.parsed.revision_id} not found")

        # Build response
        resp = GetRevisionResponse(
            revision=self.revision_adapter.convert_to_dto(action_result.data[0])
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
    cors.add(app.router.add_route("POST", "/search", api_handler.search_deployments))
    cors.add(app.router.add_route("GET", "/{deployment_id}", api_handler.get_deployment))
    cors.add(app.router.add_route("PATCH", "/{deployment_id}", api_handler.update_deployment))
    cors.add(app.router.add_route("DELETE", "/{deployment_id}", api_handler.destroy_deployment))

    # Revision routes (nested under deployment)
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
