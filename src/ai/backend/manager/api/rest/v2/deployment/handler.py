"""REST v2 handler for the deployment domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    BulkDeleteAutoScalingRulesInput,
    CreateAutoScalingRuleInput,
    DeleteAutoScalingRuleInput,
    UpdateAutoScalingRuleInput,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateRevisionInput,
    AddRevisionGQLInputDTO,
    AdminSearchDeploymentsInput,
    AdminSearchRevisionsInput,
    BulkDeleteAccessTokensInput,
    CreateAccessTokenInput,
    CreateDeploymentInput,
    DeleteAccessTokenInput,
    DeleteDeploymentInput,
    SearchAccessTokensInput,
    SearchAutoScalingRulesInput,
    SearchDeploymentPoliciesInput,
    SearchReplicasInput,
    SearchRoutesInput,
    SyncReplicaInput,
    UpdateDeploymentInput,
    UpdateRouteTrafficStatusInput,
    UpsertDeploymentPolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    SearchAllocatedResourceSlotsInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import (
    DeploymentIdPathParam,
    ProjectIdPathParam,
    ReplicaIdPathParam,
    RevisionIdPathParam,
    RuleIdPathParam,
    TokenIdPathParam,
)
from ai.backend.manager.data.deployment.types import (
    AccessTokenSearchScope,
    AutoScalingRuleSearchScope,
    ReplicaSearchScope,
    RevisionSearchScope,
    RouteSearchScope,
)
from ai.backend.manager.dto.context import UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.deployment import DeploymentAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2DeploymentHandler:
    """REST v2 handler for deployment operations."""

    def __init__(self, *, adapter: DeploymentAdapter) -> None:
        self._adapter = adapter

    # ------------------------------------------------------------------
    # Core deployment CRUD
    # ------------------------------------------------------------------

    async def create(
        self,
        user_ctx: UserContext,
        body: BodyParam[CreateDeploymentInput],
    ) -> APIResponse:
        """Create a new deployment."""
        result = await self._adapter.create(
            body.parsed,
            created_user_id=user_ctx.user_uuid,
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[AdminSearchDeploymentsInput],
    ) -> APIResponse:
        """Search deployments with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def project_search(
        self,
        path: PathParam[ProjectIdPathParam],
        body: BodyParam[AdminSearchDeploymentsInput],
    ) -> APIResponse:
        """Search deployments within a project."""
        result = await self._adapter.project_search(path.parsed.project_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_search(
        self,
        body: BodyParam[AdminSearchDeploymentsInput],
    ) -> APIResponse:
        """Search deployments owned by the current user."""
        result = await self._adapter.my_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(
        self,
        path: PathParam[DeploymentIdPathParam],
    ) -> APIResponse:
        """Retrieve a single deployment by ID."""
        result = await self._adapter.get(path.parsed.deployment_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_current_revision(
        self,
        path: PathParam[DeploymentIdPathParam],
    ) -> APIResponse:
        """Retrieve the current active revision of a deployment."""
        result = await self._adapter.get_current_revision(path.parsed.deployment_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[DeploymentIdPathParam],
        body: BodyParam[UpdateDeploymentInput],
    ) -> APIResponse:
        """Update deployment metadata and configuration."""
        result = await self._adapter.update(
            body.parsed,
            deployment_id=path.parsed.deployment_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        body: BodyParam[DeleteDeploymentInput],
    ) -> APIResponse:
        """Delete a deployment."""
        result = await self._adapter.delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------
    # Revision operations
    # ------------------------------------------------------------------

    async def add_revision(
        self,
        path: PathParam[DeploymentIdPathParam],
        body: BodyParam[AddRevisionGQLInputDTO],
    ) -> APIResponse:
        """Add a new model revision to a deployment."""
        result = await self._adapter.add_revision(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get_revision(
        self,
        path: PathParam[RevisionIdPathParam],
    ) -> APIResponse:
        """Retrieve a single revision by ID."""
        result = await self._adapter.get_revision(path.parsed.revision_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_revisions(
        self,
        path: PathParam[DeploymentIdPathParam],
        body: BodyParam[AdminSearchRevisionsInput],
    ) -> APIResponse:
        """Search revisions scoped to a specific deployment."""
        scope = RevisionSearchScope(deployment_id=path.parsed.deployment_id)
        result = await self._adapter.search_revisions(scope, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_revisions(
        self,
        body: BodyParam[AdminSearchRevisionsInput],
    ) -> APIResponse:
        """Search revisions without scope (admin, all deployments)."""
        result = await self._adapter.admin_search_revisions(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def activate_revision(
        self,
        body: BodyParam[ActivateRevisionInput],
    ) -> APIResponse:
        """Activate a specific revision as the current revision."""
        result = await self._adapter.activate_revision(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_revision_resource_slots(
        self,
        path: PathParam[RevisionIdPathParam],
        body: BodyParam[SearchAllocatedResourceSlotsInput],
    ) -> APIResponse:
        """Search resource slots allocated to a deployment revision."""
        result = await self._adapter.search_revision_resource_slots(
            revision_id=path.parsed.revision_id,
            input=body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------
    # Replica operations
    # ------------------------------------------------------------------

    async def search_replicas(
        self,
        path: PathParam[DeploymentIdPathParam],
        body: BodyParam[SearchReplicasInput],
    ) -> APIResponse:
        """Search replicas scoped to a specific deployment."""
        scope = ReplicaSearchScope(deployment_id=path.parsed.deployment_id)
        result = await self._adapter.search_replicas(scope, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_replicas(
        self,
        body: BodyParam[SearchReplicasInput],
    ) -> APIResponse:
        """Search replicas without scope (admin, all deployments)."""
        result = await self._adapter.admin_search_replicas(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_replica(
        self,
        path: PathParam[ReplicaIdPathParam],
    ) -> APIResponse:
        """Retrieve a single replica by ID."""
        result = await self._adapter.get_replica(path.parsed.replica_id)
        if result is None:
            raise web.HTTPNotFound(reason="Replica not found")
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def sync_replicas(
        self,
        body: BodyParam[SyncReplicaInput],
    ) -> APIResponse:
        """Force sync replica information for a deployment."""
        result = await self._adapter.sync_replicas(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------
    # Route operations
    # ------------------------------------------------------------------

    async def search_routes(
        self,
        path: PathParam[DeploymentIdPathParam],
        body: BodyParam[SearchRoutesInput],
    ) -> APIResponse:
        """Search routes scoped to a specific deployment."""
        scope = RouteSearchScope(deployment_id=path.parsed.deployment_id)
        result = await self._adapter.search_routes(scope, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_route_traffic(
        self,
        body: BodyParam[UpdateRouteTrafficStatusInput],
    ) -> APIResponse:
        """Update the traffic status of a route."""
        result = await self._adapter.update_route_traffic(
            body.parsed.route_id,
            body.parsed.traffic_status,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------
    # Access token operations
    # ------------------------------------------------------------------

    async def create_access_token(
        self,
        body: BodyParam[CreateAccessTokenInput],
    ) -> APIResponse:
        """Create a new access token for a deployment."""
        result = await self._adapter.create_access_token(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def search_access_tokens(
        self,
        path: PathParam[DeploymentIdPathParam],
        body: BodyParam[SearchAccessTokensInput],
    ) -> APIResponse:
        """Search access tokens scoped to a specific deployment."""
        scope = AccessTokenSearchScope(deployment_id=path.parsed.deployment_id)
        result = await self._adapter.search_access_tokens(scope, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_access_token(
        self,
        path: PathParam[TokenIdPathParam],
    ) -> APIResponse:
        """Get an access token by ID."""
        result = await self._adapter.get_access_token(path.parsed.token_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_access_token(
        self,
        body: BodyParam[DeleteAccessTokenInput],
    ) -> APIResponse:
        """Delete an access token."""
        result = await self._adapter.delete_access_token(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_delete_access_tokens(
        self,
        body: BodyParam[BulkDeleteAccessTokensInput],
    ) -> APIResponse:
        """Bulk delete access tokens."""
        result = await self._adapter.bulk_delete_access_tokens(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------
    # Auto-scaling rule operations
    # ------------------------------------------------------------------

    async def create_auto_scaling_rule(
        self,
        body: BodyParam[CreateAutoScalingRuleInput],
    ) -> APIResponse:
        """Create a new auto-scaling rule for a deployment."""
        result = await self._adapter.create_rule(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def search_auto_scaling_rules(
        self,
        path: PathParam[DeploymentIdPathParam],
        body: BodyParam[SearchAutoScalingRulesInput],
    ) -> APIResponse:
        """Search auto-scaling rules scoped to a specific deployment."""
        scope = AutoScalingRuleSearchScope(deployment_id=path.parsed.deployment_id)
        result = await self._adapter.search_rules(scope, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_auto_scaling_rule(
        self,
        path: PathParam[RuleIdPathParam],
    ) -> APIResponse:
        """Retrieve a single auto-scaling rule by ID."""
        result = await self._adapter.get_rule(path.parsed.rule_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_auto_scaling_rule(
        self,
        path: PathParam[RuleIdPathParam],
        body: BodyParam[UpdateAutoScalingRuleInput],
    ) -> APIResponse:
        """Update an auto-scaling rule."""
        result = await self._adapter.update_rule(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_auto_scaling_rule(
        self,
        body: BodyParam[DeleteAutoScalingRuleInput],
    ) -> APIResponse:
        """Delete an auto-scaling rule."""
        result = await self._adapter.delete_rule(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_delete_auto_scaling_rules(
        self,
        body: BodyParam[BulkDeleteAutoScalingRulesInput],
    ) -> APIResponse:
        """Bulk delete auto-scaling rules."""
        result = await self._adapter.bulk_delete_rules(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------
    # Deployment policy operations
    # ------------------------------------------------------------------

    async def get_deployment_policy(
        self,
        path: PathParam[DeploymentIdPathParam],
    ) -> APIResponse:
        """Retrieve a deployment policy by deployment ID."""
        result = await self._adapter.get_policy(path.parsed.deployment_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_deployment_policies(
        self,
        body: BodyParam[SearchDeploymentPoliciesInput],
    ) -> APIResponse:
        """Search deployment policies with filters and pagination."""
        result = await self._adapter.search_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def upsert_deployment_policy(
        self,
        body: BodyParam[UpsertDeploymentPolicyInput],
    ) -> APIResponse:
        """Create or update a deployment policy."""
        result = await self._adapter.upsert_policy(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
