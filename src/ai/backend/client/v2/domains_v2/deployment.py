"""V2 REST SDK client for the deployment domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    CreateAutoScalingRuleInput,
    DeleteAutoScalingRuleInput,
    UpdateAutoScalingRuleInput,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ActivateRevisionInput,
    AddRevisionGQLInputDTO,
    AdminSearchDeploymentsInput,
    AdminSearchRevisionsInput,
    CreateAccessTokenInput,
    CreateDeploymentInput,
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
from ai.backend.common.dto.manager.v2.deployment.response import (
    ActivateRevisionPayload,
    AddRevisionPayload,
    AdminSearchDeploymentsPayload,
    AdminSearchRevisionsPayload,
    CreateAccessTokenPayload,
    CreateAutoScalingRulePayload,
    CreateDeploymentPayload,
    DeleteAutoScalingRulePayload,
    DeleteDeploymentPayload,
    DeploymentNode,
    GetAutoScalingRulePayload,
    GetDeploymentPolicyPayload,
    ReplicaNode,
    RevisionNode,
    SearchAccessTokensPayload,
    SearchAutoScalingRulesPayload,
    SearchDeploymentPoliciesPayload,
    SearchReplicasPayload,
    SearchRoutesPayload,
    SyncReplicaPayload,
    UpdateAutoScalingRulePayload,
    UpdateDeploymentPayload,
    UpdateRouteTrafficStatusPayload,
    UpsertDeploymentPolicyPayload,
)

_PATH = "/v2/deployments"


class V2DeploymentClient(BaseDomainClient):
    """SDK client for the deployment REST v2 endpoints."""

    # ------------------------------------------------------------------
    # Core deployment CRUD
    # ------------------------------------------------------------------

    async def create(
        self,
        body: CreateDeploymentInput,
    ) -> CreateDeploymentPayload:
        """Create a new deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/",
            request=body,
            response_model=CreateDeploymentPayload,
        )

    async def admin_search(
        self,
        body: AdminSearchDeploymentsInput,
    ) -> AdminSearchDeploymentsPayload:
        """Search deployments with admin scope (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/search",
            request=body,
            response_model=AdminSearchDeploymentsPayload,
        )

    async def get(
        self,
        deployment_id: UUID,
    ) -> DeploymentNode:
        """Retrieve a single deployment by ID."""
        return await self._client.typed_request(
            "GET",
            _PATH + f"/{deployment_id}",
            response_model=DeploymentNode,
        )

    async def update(
        self,
        deployment_id: UUID,
        body: UpdateDeploymentInput,
    ) -> UpdateDeploymentPayload:
        """Update deployment metadata and configuration."""
        return await self._client.typed_request(
            "PUT",
            _PATH + f"/{deployment_id}",
            request=body,
            response_model=UpdateDeploymentPayload,
        )

    async def delete(
        self,
        body: DeleteDeploymentInput,
    ) -> DeleteDeploymentPayload:
        """Delete a deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/delete",
            request=body,
            response_model=DeleteDeploymentPayload,
        )

    # ------------------------------------------------------------------
    # Revision operations
    # ------------------------------------------------------------------

    async def add_revision(
        self,
        deployment_id: UUID,
        body: AddRevisionGQLInputDTO,
    ) -> AddRevisionPayload:
        """Add a new model revision to a deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + f"/{deployment_id}/revisions",
            request=body,
            response_model=AddRevisionPayload,
        )

    async def get_current_revision(
        self,
        deployment_id: UUID,
    ) -> RevisionNode:
        """Retrieve the current active revision of a deployment."""
        return await self._client.typed_request(
            "GET",
            _PATH + f"/{deployment_id}/current-revision",
            response_model=RevisionNode,
        )

    async def get_revision(
        self,
        revision_id: UUID,
    ) -> RevisionNode:
        """Retrieve a single revision by ID."""
        return await self._client.typed_request(
            "GET",
            _PATH + f"/revisions/{revision_id}",
            response_model=RevisionNode,
        )

    async def search_revisions(
        self,
        deployment_id: UUID,
        body: AdminSearchRevisionsInput,
    ) -> AdminSearchRevisionsPayload:
        """Search revisions scoped to a specific deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + f"/{deployment_id}/revisions/search",
            request=body,
            response_model=AdminSearchRevisionsPayload,
        )

    async def admin_search_revisions(
        self,
        body: AdminSearchRevisionsInput,
    ) -> AdminSearchRevisionsPayload:
        """Search revisions without scope (admin, all deployments)."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/revisions/search",
            request=body,
            response_model=AdminSearchRevisionsPayload,
        )

    async def activate_revision(
        self,
        body: ActivateRevisionInput,
    ) -> ActivateRevisionPayload:
        """Activate a specific revision as the current revision."""
        return await self._client.typed_request(
            "POST",
            _PATH + f"/{body.deployment_id}/revisions/activate",
            request=body,
            response_model=ActivateRevisionPayload,
        )

    # ------------------------------------------------------------------
    # Replica operations
    # ------------------------------------------------------------------

    async def search_replicas(
        self,
        deployment_id: UUID,
        body: SearchReplicasInput,
    ) -> SearchReplicasPayload:
        """Search replicas scoped to a specific deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + f"/{deployment_id}/replicas/search",
            request=body,
            response_model=SearchReplicasPayload,
        )

    async def admin_search_replicas(
        self,
        body: SearchReplicasInput,
    ) -> SearchReplicasPayload:
        """Search replicas without scope (admin, all deployments)."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/replicas/search",
            request=body,
            response_model=SearchReplicasPayload,
        )

    async def get_replica(
        self,
        replica_id: UUID,
    ) -> ReplicaNode:
        """Retrieve a single replica by ID."""
        return await self._client.typed_request(
            "GET",
            _PATH + f"/replicas/{replica_id}",
            response_model=ReplicaNode,
        )

    async def sync_replicas(
        self,
        body: SyncReplicaInput,
    ) -> SyncReplicaPayload:
        """Force sync replica information for a deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + f"/{body.model_deployment_id}/replicas/sync",
            request=body,
            response_model=SyncReplicaPayload,
        )

    # ------------------------------------------------------------------
    # Route operations
    # ------------------------------------------------------------------

    async def search_routes(
        self,
        deployment_id: UUID,
        body: SearchRoutesInput,
    ) -> SearchRoutesPayload:
        """Search routes scoped to a specific deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + f"/{deployment_id}/routes/search",
            request=body,
            response_model=SearchRoutesPayload,
        )

    async def update_route_traffic(
        self,
        body: UpdateRouteTrafficStatusInput,
    ) -> UpdateRouteTrafficStatusPayload:
        """Update the traffic status of a route."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/routes/update-traffic",
            request=body,
            response_model=UpdateRouteTrafficStatusPayload,
        )

    # ------------------------------------------------------------------
    # Access token operations
    # ------------------------------------------------------------------

    async def create_access_token(
        self,
        deployment_id: UUID,
        body: CreateAccessTokenInput,
    ) -> CreateAccessTokenPayload:
        """Create a new access token for a deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + f"/{deployment_id}/access-tokens",
            request=body,
            response_model=CreateAccessTokenPayload,
        )

    async def search_access_tokens(
        self,
        deployment_id: UUID,
        body: SearchAccessTokensInput,
    ) -> SearchAccessTokensPayload:
        """Search access tokens scoped to a specific deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + f"/{deployment_id}/access-tokens/search",
            request=body,
            response_model=SearchAccessTokensPayload,
        )

    # ------------------------------------------------------------------
    # Auto-scaling rule operations
    # ------------------------------------------------------------------

    async def create_auto_scaling_rule(
        self,
        body: CreateAutoScalingRuleInput,
    ) -> CreateAutoScalingRulePayload:
        """Create a new auto-scaling rule for a deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/auto-scaling-rules",
            request=body,
            response_model=CreateAutoScalingRulePayload,
        )

    async def search_auto_scaling_rules(
        self,
        deployment_id: UUID,
        body: SearchAutoScalingRulesInput,
    ) -> SearchAutoScalingRulesPayload:
        """Search auto-scaling rules scoped to a specific deployment."""
        return await self._client.typed_request(
            "POST",
            _PATH + f"/{deployment_id}/auto-scaling-rules/search",
            request=body,
            response_model=SearchAutoScalingRulesPayload,
        )

    async def get_auto_scaling_rule(
        self,
        rule_id: UUID,
    ) -> GetAutoScalingRulePayload:
        """Retrieve a single auto-scaling rule by ID."""
        return await self._client.typed_request(
            "GET",
            _PATH + f"/auto-scaling-rules/{rule_id}",
            response_model=GetAutoScalingRulePayload,
        )

    async def update_auto_scaling_rule(
        self,
        rule_id: UUID,
        body: UpdateAutoScalingRuleInput,
    ) -> UpdateAutoScalingRulePayload:
        """Update an auto-scaling rule."""
        return await self._client.typed_request(
            "PUT",
            _PATH + f"/auto-scaling-rules/{rule_id}",
            request=body,
            response_model=UpdateAutoScalingRulePayload,
        )

    async def delete_auto_scaling_rule(
        self,
        body: DeleteAutoScalingRuleInput,
    ) -> DeleteAutoScalingRulePayload:
        """Delete an auto-scaling rule."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/auto-scaling-rules/delete",
            request=body,
            response_model=DeleteAutoScalingRulePayload,
        )

    # ------------------------------------------------------------------
    # Deployment policy operations
    # ------------------------------------------------------------------

    async def get_deployment_policy(
        self,
        deployment_id: UUID,
    ) -> GetDeploymentPolicyPayload:
        """Retrieve a deployment policy by deployment ID (superadmin only)."""
        return await self._client.typed_request(
            "GET",
            _PATH + f"/policies/{deployment_id}",
            response_model=GetDeploymentPolicyPayload,
        )

    async def search_deployment_policies(
        self,
        body: SearchDeploymentPoliciesInput,
    ) -> SearchDeploymentPoliciesPayload:
        """Search deployment policies (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/policies/search",
            request=body,
            response_model=SearchDeploymentPoliciesPayload,
        )

    async def upsert_deployment_policy(
        self,
        body: UpsertDeploymentPolicyInput,
    ) -> UpsertDeploymentPolicyPayload:
        """Create or update a deployment policy (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            _PATH + "/policies/upsert",
            request=body,
            response_model=UpsertDeploymentPolicyPayload,
        )
