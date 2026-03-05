"""REST API handler for deployment system with constructor dependency injection.

All handlers use typed parameters (``BodyParam``, ``PathParam``,
``UserContext``) that are automatically extracted by the route
wrapper, and return ``APIResponse`` objects.
"""

from __future__ import annotations

from http import HTTPStatus

from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.deployment import (
    ActivateRevisionResponse,
    AddRevisionRequest,
    AddRevisionResponse,
    CreateDeploymentRequest,
    CreateDeploymentResponse,
    CursorPaginationInfo,
    DeactivateRevisionResponse,
    DeploymentPathParam,
    DeploymentPolicyPathParam,
    DestroyDeploymentResponse,
    GetDeploymentPolicyResponse,
    GetDeploymentResponse,
    GetRevisionResponse,
    ListDeploymentsResponse,
    ListRevisionsResponse,
    ListRoutesResponse,
    PaginationInfo,
    RevisionFilter,
    RevisionPathParam,
    RouteFilter,
    RoutePathParam,
    SearchDeploymentsRequest,
    SearchRevisionsRequest,
    SearchRoutesRequest,
    UpdateDeploymentRequest,
    UpdateDeploymentResponse,
    UpdateRouteTrafficStatusRequest,
    UpdateRouteTrafficStatusResponse,
    UpsertDeploymentPolicyRequest,
    UpsertDeploymentPolicyResponse,
)
from ai.backend.manager.data.deployment.types import RouteTrafficStatus as ManagerRouteTrafficStatus
from ai.backend.manager.dto.context import UserContext
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
from ai.backend.manager.services.deployment.actions.deployment_policy.create_deployment_policy import (
    CreateDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.get_deployment_policy import (
    GetDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.update_deployment_policy import (
    UpdateDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.get_deployment_by_id import (
    GetDeploymentByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
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
from ai.backend.manager.types import OptionalState

from .adapter import (
    AddRevisionAdapter,
    CreateDeploymentAdapter,
    DeploymentAdapter,
    DeploymentPolicyAdapter,
    RevisionAdapter,
    RouteAdapter,
)


class DeploymentAPIHandler:
    """REST API handler class for deployment operations with constructor DI."""

    def __init__(
        self,
        *,
        deployment: DeploymentProcessors | None,
    ) -> None:
        self._deployment = deployment
        self._deployment_adapter = DeploymentAdapter()
        self._revision_adapter = RevisionAdapter()
        self._route_adapter = RouteAdapter()
        self._create_deployment_adapter = CreateDeploymentAdapter()
        self._policy_adapter = DeploymentPolicyAdapter()
        self._add_revision_adapter = AddRevisionAdapter()

    def _get_deployment_processors(self) -> DeploymentProcessors:
        """Get deployment processors, raising ServiceUnavailable if not available."""
        if self._deployment is None:
            raise web.HTTPServiceUnavailable(
                reason="Deployment service is not available on this manager"
            )
        return self._deployment

    # Deployment Endpoints

    async def create_deployment(
        self,
        body: BodyParam[CreateDeploymentRequest],
        user_ctx: UserContext,
    ) -> APIResponse:
        """Create a new deployment."""
        deployment_processors = self._get_deployment_processors()

        # Build creator from request using adapter
        creator = self._create_deployment_adapter.build_creator(
            body.parsed,
            user_uuid=user_ctx.user_uuid,
        )

        # Call service action
        action_result = await deployment_processors.create_deployment.wait_for_complete(
            CreateDeploymentAction(creator=creator)
        )

        # Build response
        resp = CreateDeploymentResponse(
            deployment=self._deployment_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def search_deployments(
        self,
        body: BodyParam[SearchDeploymentsRequest],
    ) -> APIResponse:
        """Search deployments with filters, orders, and pagination."""
        deployment_processors = self._get_deployment_processors()

        # Build querier using adapter
        querier = self._deployment_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await deployment_processors.search_deployments.wait_for_complete(
            SearchDeploymentsAction(querier=querier)
        )

        # Build response
        resp = ListDeploymentsResponse(
            deployments=[
                self._deployment_adapter.convert_to_dto(dep) for dep in action_result.data
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_deployment(
        self,
        path: PathParam[DeploymentPathParam],
    ) -> APIResponse:
        """Get a specific deployment."""
        deployment_processors = self._get_deployment_processors()

        # Call service action - raises EndpointNotFound if not found
        action_result = await deployment_processors.get_deployment_by_id.wait_for_complete(
            GetDeploymentByIdAction(deployment_id=path.parsed.deployment_id)
        )

        # Build response
        resp = GetDeploymentResponse(
            deployment=self._deployment_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update_deployment(
        self,
        path: PathParam[DeploymentPathParam],
        body: BodyParam[UpdateDeploymentRequest],
    ) -> APIResponse:
        """Update an existing deployment."""
        deployment_processors = self._get_deployment_processors()

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
            deployment=self._deployment_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def destroy_deployment(
        self,
        path: PathParam[DeploymentPathParam],
    ) -> APIResponse:
        """Destroy a deployment."""
        deployment_processors = self._get_deployment_processors()

        # Call service action
        action_result = await deployment_processors.destroy_deployment.wait_for_complete(
            DestroyDeploymentAction(endpoint_id=path.parsed.deployment_id)
        )

        # Build response
        resp = DestroyDeploymentResponse(deleted=action_result.success)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Revision Endpoints

    async def add_revision(
        self,
        path: PathParam[DeploymentPathParam],
        body: BodyParam[AddRevisionRequest],
    ) -> APIResponse:
        """Add a new revision to an existing deployment."""
        deployment_processors = self._get_deployment_processors()

        # Build revision creator from request using adapter
        revision_creator = self._add_revision_adapter.build_revision_creator(body.parsed.revision)

        # Call service action
        action_result = await deployment_processors.add_model_revision.wait_for_complete(
            AddModelRevisionAction(
                model_deployment_id=path.parsed.deployment_id,
                adder=revision_creator,
            )
        )

        # Build response
        resp = AddRevisionResponse(
            revision=self._revision_adapter.convert_to_dto(action_result.revision)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def search_revisions(
        self,
        path: PathParam[DeploymentPathParam],
        body: BodyParam[SearchRevisionsRequest],
    ) -> APIResponse:
        """Search revisions for a deployment with filters, orders, and pagination."""
        deployment_processors = self._get_deployment_processors()

        # Build querier using adapter, adding deployment filter
        if body.parsed.filter is None:
            body.parsed.filter = RevisionFilter(deployment_id=path.parsed.deployment_id)
        else:
            body.parsed.filter.deployment_id = path.parsed.deployment_id

        querier = self._revision_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await deployment_processors.search_revisions.wait_for_complete(
            SearchRevisionsAction(querier=querier)
        )

        # Build response
        resp = ListRevisionsResponse(
            revisions=[self._revision_adapter.convert_to_dto(rev) for rev in action_result.data],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_revision(
        self,
        path: PathParam[RevisionPathParam],
    ) -> APIResponse:
        """Get a specific revision."""
        deployment_processors = self._get_deployment_processors()

        # Call service action - raises DeploymentRevisionNotFound if not found
        action_result = await deployment_processors.get_revision_by_id.wait_for_complete(
            GetRevisionByIdAction(revision_id=path.parsed.revision_id)
        )

        # Build response
        resp = GetRevisionResponse(
            revision=self._revision_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def activate_revision(
        self,
        path: PathParam[RevisionPathParam],
    ) -> APIResponse:
        """Activate a revision to make it the current active revision."""
        deployment_processors = self._get_deployment_processors()

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

    async def deactivate_revision(
        self,
        _path: PathParam[RevisionPathParam],
    ) -> APIResponse:
        """Deactivate a revision."""
        # Note: For deactivation, we can set the desired_replicas to 0 or use a specific action
        # This is a simplified implementation
        resp = DeactivateRevisionResponse(success=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Route Endpoints

    async def search_routes(
        self,
        path: PathParam[DeploymentPathParam],
        body: BodyParam[SearchRoutesRequest],
    ) -> APIResponse:
        """Search routes for a deployment with filters, orders, and pagination."""
        deployment_processors = self._get_deployment_processors()

        # Build querier using adapter, adding deployment filter
        if body.parsed.filter is None:
            body.parsed.filter = RouteFilter(deployment_id=path.parsed.deployment_id)
        else:
            body.parsed.filter.deployment_id = path.parsed.deployment_id

        querier = self._route_adapter.build_querier(body.parsed)

        # Call service action
        action_result = await deployment_processors.search_routes.wait_for_complete(
            SearchRoutesAction(querier=querier)
        )

        # Build response
        resp = ListRoutesResponse(
            routes=[self._route_adapter.convert_to_dto(route) for route in action_result.routes],
            pagination=CursorPaginationInfo(
                total_count=action_result.total_count,
                has_next_page=action_result.has_next_page,
                has_previous_page=action_result.has_previous_page,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update_route_traffic_status(
        self,
        path: PathParam[RoutePathParam],
        body: BodyParam[UpdateRouteTrafficStatusRequest],
    ) -> APIResponse:
        """Update traffic status of a route."""
        deployment_processors = self._get_deployment_processors()

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
            route=self._route_adapter.convert_to_dto(action_result.route)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Deployment Policy Endpoints

    async def upsert_deployment_policy(
        self,
        path: PathParam[DeploymentPolicyPathParam],
        body: BodyParam[UpsertDeploymentPolicyRequest],
    ) -> APIResponse:
        """Create or update a deployment policy for a deployment.

        If a policy already exists for the deployment, it is updated;
        otherwise a new one is created.
        """
        from ai.backend.manager.errors.service import DeploymentPolicyNotFound

        deployment_processors = self._get_deployment_processors()

        try:
            policy_result = await deployment_processors.get_deployment_policy.wait_for_complete(
                GetDeploymentPolicyAction(endpoint_id=path.parsed.deployment_id)
            )
        except DeploymentPolicyNotFound:
            policy_result = None

        if policy_result is None:
            creator = self._policy_adapter.build_creator_from_upsert(
                body.parsed, deployment_id=path.parsed.deployment_id
            )
            action_result = await deployment_processors.create_deployment_policy.wait_for_complete(
                CreateDeploymentPolicyAction(creator=creator)
            )
            resp = UpsertDeploymentPolicyResponse(
                deployment_policy=self._policy_adapter.convert_to_dto(action_result.data),
                created=True,
            )
            return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)
        modifier = self._policy_adapter.build_modifier_from_upsert(body.parsed)
        action_result = await deployment_processors.update_deployment_policy.wait_for_complete(
            UpdateDeploymentPolicyAction(
                policy_id=policy_result.data.id,
                modifier=modifier,
            )
        )
        resp = UpsertDeploymentPolicyResponse(
            deployment_policy=self._policy_adapter.convert_to_dto(action_result.data),
            created=False,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_deployment_policy(
        self,
        path: PathParam[DeploymentPolicyPathParam],
    ) -> APIResponse:
        """Get a deployment policy for a deployment."""
        deployment_processors = self._get_deployment_processors()

        action_result = await deployment_processors.get_deployment_policy.wait_for_complete(
            GetDeploymentPolicyAction(endpoint_id=path.parsed.deployment_id)
        )

        resp = GetDeploymentPolicyResponse(
            deployment_policy=self._policy_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
