"""Deployment service processors for GraphQL API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import FieldOwnerLookupOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.services.deployment.actions.access_token.bulk_delete_access_tokens import (
    BulkDeleteAccessTokensAction,
    BulkDeleteAccessTokensActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
    CreateAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.delete_access_token import (
    DeleteAccessTokenAction,
    DeleteAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.get_access_token import (
    GetAccessTokenAction,
    GetAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.global_search_access_tokens import (
    GlobalSearchAccessTokensAction,
    GlobalSearchAccessTokensActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.search_access_tokens import (
    SearchAccessTokensAction,
    SearchAccessTokensActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.bulk_delete_auto_scaling_rules import (
    BulkDeleteAutoScalingRulesAction,
    BulkDeleteAutoScalingRulesActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
    CreateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
    DeleteAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.get_auto_scaling_rule import (
    GetAutoScalingRuleAction,
    GetAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.search_auto_scaling_rules import (
    SearchAutoScalingRulesAction,
    SearchAutoScalingRulesActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.update_auto_scaling_rule import (
    UpdateAutoScalingRuleAction,
    UpdateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.create_legacy_deployment import (
    CreateLegacyDeploymentAction,
    CreateLegacyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.deployment_policy import (
    GetDeploymentPolicyAction,
    GetDeploymentPolicyActionResult,
    SearchDeploymentPoliciesAction,
    SearchDeploymentPoliciesActionResult,
    UpsertDeploymentPolicyAction,
    UpsertDeploymentPolicyActionResult,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.get_deployment_by_id import (
    GetDeploymentByIdAction,
    GetDeploymentByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.get_legacy_deployment_by_id import (
    GetLegacyDeploymentByIdAction,
    GetLegacyDeploymentByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.get_replica_by_id import (
    GetReplicaByIdAction,
    GetReplicaByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.global_search_replicas import (
    GlobalSearchReplicasAction,
    GlobalSearchReplicasActionResult,
)
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupAccessTokenDeploymentAction,
    LookupAutoScalingRuleDeploymentAction,
    LookupRevisionDeploymentAction,
    LookupRouteDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
    AddModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
    GetRevisionByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.global_search_revisions import (
    GlobalSearchRevisionsAction,
    GlobalSearchRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revision_resource_slots import (
    SearchRevisionResourceSlotsAction,
    SearchRevisionResourceSlotsActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
    SearchRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.refresh_deployment_revisions import (
    GlobalRefreshDeploymentRevisionsAction,
    GlobalRefreshDeploymentRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.replace_deployment_options import (
    ReplaceDeploymentOptionsAction,
    ReplaceDeploymentOptionsActionResult,
)
from ai.backend.manager.services.deployment.actions.revision_operations import (
    ActivateRevisionAction,
    ActivateRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.route import (
    SearchRoutesAction,
    SearchRoutesActionResult,
    UpdateRouteTrafficStatusAction,
    UpdateRouteTrafficStatusActionResult,
)
from ai.backend.manager.services.deployment.actions.search_deployments import (
    GlobalSearchDeploymentsAction,
    GlobalSearchDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.search_deployments_in_project import (
    SearchDeploymentsInProjectAction,
    SearchDeploymentsInProjectActionResult,
)
from ai.backend.manager.services.deployment.actions.search_legacy_deployments import (
    GlobalSearchLegacyDeploymentsAction,
    GlobalSearchLegacyDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.search_replicas import (
    SearchReplicasAction,
    SearchReplicasActionResult,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import (
    SyncReplicaAction,
    SyncReplicaActionResult,
)
from ai.backend.manager.services.deployment.actions.update_deployment import (
    UpdateDeploymentAction,
    UpdateDeploymentActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.deployment.service import DeploymentService


class DeploymentProcessors:
    """Processors for deployment operations."""

    lookup_auto_scaling_rule_deployment: LookupActionProcessor[
        LookupAutoScalingRuleDeploymentAction, FieldOwnerLookupOpsResult
    ]
    lookup_access_token_deployment: LookupActionProcessor[
        LookupAccessTokenDeploymentAction, FieldOwnerLookupOpsResult
    ]
    lookup_route_deployment: LookupActionProcessor[
        LookupRouteDeploymentAction, FieldOwnerLookupOpsResult
    ]
    lookup_revision_deployment: LookupActionProcessor[
        LookupRevisionDeploymentAction, FieldOwnerLookupOpsResult
    ]

    # Deployment CRUD
    create_deployment: ScopeActionProcessor[CreateDeploymentAction, CreateDeploymentActionResult]
    create_legacy_deployment: ScopeActionProcessor[
        CreateLegacyDeploymentAction, CreateLegacyDeploymentActionResult
    ]
    update_deployment: SingleEntityActionProcessor[
        UpdateDeploymentAction, UpdateDeploymentActionResult
    ]
    replace_deployment_options: SingleEntityActionProcessor[
        ReplaceDeploymentOptionsAction, ReplaceDeploymentOptionsActionResult
    ]
    destroy_deployment: SingleEntityActionProcessor[
        DestroyDeploymentAction, DestroyDeploymentActionResult
    ]
    global_search: GlobalActionProcessor[
        GlobalSearchDeploymentsAction, GlobalSearchDeploymentsActionResult
    ]
    # Legacy (REST v1) read variants — full revision. DO NOT USE in new code.
    global_search_legacy: GlobalActionProcessor[
        GlobalSearchLegacyDeploymentsAction, GlobalSearchLegacyDeploymentsActionResult
    ]
    search_deployments_in_project: ScopeActionProcessor[
        SearchDeploymentsInProjectAction, SearchDeploymentsInProjectActionResult
    ]
    get_deployment_by_id: SingleEntityActionProcessor[
        GetDeploymentByIdAction, GetDeploymentByIdActionResult
    ]
    get_legacy_deployment_by_id: SingleEntityActionProcessor[
        GetLegacyDeploymentByIdAction, GetLegacyDeploymentByIdActionResult
    ]
    get_deployment_policy: SingleEntityActionProcessor[
        GetDeploymentPolicyAction, GetDeploymentPolicyActionResult
    ]
    search_deployment_policies: GlobalActionProcessor[
        SearchDeploymentPoliciesAction, SearchDeploymentPoliciesActionResult
    ]
    upsert_deployment_policy: SingleEntityActionProcessor[
        UpsertDeploymentPolicyAction, UpsertDeploymentPolicyActionResult
    ]

    # Revision operations
    add_model_revision: SingleEntityActionProcessor[
        AddModelRevisionAction, AddModelRevisionActionResult
    ]
    get_revision_by_id: SingleEntityActionProcessor[
        GetRevisionByIdAction, GetRevisionByIdActionResult
    ]
    search_revisions: SingleEntityActionProcessor[
        SearchRevisionsAction, SearchRevisionsActionResult
    ]
    search_revision_resource_slots: GlobalActionProcessor[
        SearchRevisionResourceSlotsAction, SearchRevisionResourceSlotsActionResult
    ]
    activate_revision: SingleEntityActionProcessor[
        ActivateRevisionAction, ActivateRevisionActionResult
    ]
    global_refresh_revisions: GlobalActionProcessor[
        GlobalRefreshDeploymentRevisionsAction, GlobalRefreshDeploymentRevisionsActionResult
    ]

    # Route operations
    sync_replicas: SingleEntityActionProcessor[SyncReplicaAction, SyncReplicaActionResult]
    search_routes: GlobalActionProcessor[SearchRoutesAction, SearchRoutesActionResult]
    update_route_traffic_status: SingleEntityActionProcessor[
        UpdateRouteTrafficStatusAction, UpdateRouteTrafficStatusActionResult
    ]

    # Replica operations
    get_replica_by_id: SingleEntityActionProcessor[GetReplicaByIdAction, GetReplicaByIdActionResult]
    search_replicas: SingleEntityActionProcessor[SearchReplicasAction, SearchReplicasActionResult]

    # Auto-scaling rules
    create_auto_scaling_rule: SingleEntityActionProcessor[
        CreateAutoScalingRuleAction, CreateAutoScalingRuleActionResult
    ]
    get_auto_scaling_rule: SingleEntityActionProcessor[
        GetAutoScalingRuleAction, GetAutoScalingRuleActionResult
    ]
    update_auto_scaling_rule: SingleEntityActionProcessor[
        UpdateAutoScalingRuleAction, UpdateAutoScalingRuleActionResult
    ]
    delete_auto_scaling_rule: SingleEntityActionProcessor[
        DeleteAutoScalingRuleAction, DeleteAutoScalingRuleActionResult
    ]
    bulk_delete_auto_scaling_rules: GlobalActionProcessor[
        BulkDeleteAutoScalingRulesAction, BulkDeleteAutoScalingRulesActionResult
    ]
    search_auto_scaling_rules: GlobalActionProcessor[
        SearchAutoScalingRulesAction, SearchAutoScalingRulesActionResult
    ]

    # Access token
    create_access_token: SingleEntityActionProcessor[
        CreateAccessTokenAction, CreateAccessTokenActionResult
    ]
    get_access_token: SingleEntityActionProcessor[GetAccessTokenAction, GetAccessTokenActionResult]
    delete_access_token: SingleEntityActionProcessor[
        DeleteAccessTokenAction, DeleteAccessTokenActionResult
    ]
    bulk_delete_access_tokens: GlobalActionProcessor[
        BulkDeleteAccessTokensAction, BulkDeleteAccessTokensActionResult
    ]
    search_access_tokens: SingleEntityActionProcessor[
        SearchAccessTokensAction, SearchAccessTokensActionResult
    ]

    global_search_replicas: GlobalActionProcessor[
        GlobalSearchReplicasAction, GlobalSearchReplicasActionResult
    ]
    global_search_revisions: GlobalActionProcessor[
        GlobalSearchRevisionsAction, GlobalSearchRevisionsActionResult
    ]
    global_search_access_tokens: GlobalActionProcessor[
        GlobalSearchAccessTokensAction, GlobalSearchAccessTokensActionResult
    ]

    def __init__(
        self, group: ProcessorGroup[ModelDeploymentData], service: DeploymentService
    ) -> None:
        self.lookup_auto_scaling_rule_deployment = group.key_owner_lookup_ops(
            LookupAutoScalingRuleDeploymentAction
        )
        self.lookup_access_token_deployment = group.key_owner_lookup_ops(
            LookupAccessTokenDeploymentAction
        )
        self.lookup_route_deployment = group.key_owner_lookup_ops(LookupRouteDeploymentAction)
        self.lookup_revision_deployment = group.key_owner_lookup_ops(LookupRevisionDeploymentAction)
        self.global_search_replicas = group.global_scope(
            GlobalSearchReplicasAction, service.global_search_replicas
        )
        self.global_search_revisions = group.global_scope(
            GlobalSearchRevisionsAction, service.global_search_revisions
        )
        self.global_search_access_tokens = group.global_scope(
            GlobalSearchAccessTokensAction, service.global_search_access_tokens
        )
        # Deployment CRUD
        self.create_deployment = group.scope(CreateDeploymentAction, service.create_deployment)
        self.create_legacy_deployment = group.scope(
            CreateLegacyDeploymentAction, service.create_legacy_deployment
        )
        self.update_deployment = group.single_entity(
            UpdateDeploymentAction, service.update_deployment
        )
        self.replace_deployment_options = group.single_entity(
            ReplaceDeploymentOptionsAction, service.replace_deployment_options
        )
        self.destroy_deployment = group.single_entity(
            DestroyDeploymentAction, service.destroy_deployment
        )
        self.global_search = group.global_scope(
            GlobalSearchDeploymentsAction, service.search_deployments
        )
        self.global_search_legacy = group.global_scope(
            GlobalSearchLegacyDeploymentsAction, service.search_legacy_deployments
        )
        self.search_deployments_in_project = group.scope(
            SearchDeploymentsInProjectAction, service.search_deployments_in_project
        )
        self.get_deployment_by_id = group.single_entity(
            GetDeploymentByIdAction, service.get_deployment_by_id
        )
        self.get_legacy_deployment_by_id = group.single_entity(
            GetLegacyDeploymentByIdAction, service.get_legacy_deployment_by_id
        )
        self.get_deployment_policy = group.single_entity(
            GetDeploymentPolicyAction, service.get_deployment_policy
        )
        self.search_deployment_policies = group.global_scope(
            SearchDeploymentPoliciesAction, service.search_deployment_policies
        )
        self.upsert_deployment_policy = group.single_entity(
            UpsertDeploymentPolicyAction, service.upsert_deployment_policy
        )

        # Revision operations
        self.add_model_revision = group.single_entity(
            AddModelRevisionAction, service.add_model_revision
        )
        self.get_revision_by_id = group.single_entity(
            GetRevisionByIdAction, service.get_revision_by_id
        )
        self.search_revisions = group.single_entity(SearchRevisionsAction, service.search_revisions)
        self.search_revision_resource_slots = group.global_scope(
            SearchRevisionResourceSlotsAction, service.search_revision_resource_slots
        )
        self.activate_revision = group.single_entity(
            ActivateRevisionAction, service.activate_revision
        )
        self.global_refresh_revisions = group.global_scope(
            GlobalRefreshDeploymentRevisionsAction, service.global_refresh_revisions
        )

        # Route operations
        self.sync_replicas = group.single_entity(SyncReplicaAction, service.sync_replicas)
        self.search_routes = group.global_scope(SearchRoutesAction, service.search_routes)
        self.update_route_traffic_status = group.single_entity(
            UpdateRouteTrafficStatusAction, service.update_route_traffic_status
        )

        # Replica operations
        self.get_replica_by_id = group.single_entity(
            GetReplicaByIdAction, service.get_replica_by_id
        )
        self.search_replicas = group.single_entity(SearchReplicasAction, service.search_replicas)

        # Auto-scaling rules
        self.create_auto_scaling_rule = group.single_entity(
            CreateAutoScalingRuleAction, service.create_auto_scaling_rule
        )
        self.get_auto_scaling_rule = group.single_entity(
            GetAutoScalingRuleAction, service.get_auto_scaling_rule
        )
        self.update_auto_scaling_rule = group.single_entity(
            UpdateAutoScalingRuleAction, service.update_auto_scaling_rule
        )
        self.delete_auto_scaling_rule = group.single_entity(
            DeleteAutoScalingRuleAction, service.delete_auto_scaling_rule
        )
        self.bulk_delete_auto_scaling_rules = group.global_scope(
            BulkDeleteAutoScalingRulesAction, service.bulk_delete_auto_scaling_rules
        )
        self.search_auto_scaling_rules = group.global_scope(
            SearchAutoScalingRulesAction, service.search_auto_scaling_rules
        )

        # Access token
        self.create_access_token = group.single_entity(
            CreateAccessTokenAction, service.create_access_token
        )
        self.get_access_token = group.single_entity(GetAccessTokenAction, service.get_access_token)
        self.delete_access_token = group.single_entity(
            DeleteAccessTokenAction, service.delete_access_token
        )
        self.bulk_delete_access_tokens = group.global_scope(
            BulkDeleteAccessTokensAction, service.bulk_delete_access_tokens
        )
        self.search_access_tokens = group.single_entity(
            SearchAccessTokensAction, service.search_access_tokens
        )
