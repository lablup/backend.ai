"""Deployment service processors for GraphQL API."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.data.entity.auto_scaling_rule import AutoScalingRuleFieldType
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyFieldType
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionFieldType
from ai.backend.common.data.entity.deployment_token import DeploymentTokenFieldType
from ai.backend.common.data.entity.replica import ReplicaFieldType
from ai.backend.common.data.entity.replica_group import ReplicaGroupFieldType
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.bulk_processor import PartialBulkFieldActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    EntityOpsResult,
    FieldOwnerLookupOpsResult,
    OwnedFieldsOpsResult,
    ScopedBatchOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.deployment.types import (
    DeploymentPolicyData,
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelDeploymentData,
    ModelReplicaData,
    ModelRevisionData,
    ReplicaGroupData,
    RouteInfo,
)
from ai.backend.manager.services.deployment.actions.access_token.bulk_delete_access_tokens import (
    BulkDeleteAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.access_token.bulk_get_access_tokens import (
    BulkGetAccessTokensAction,
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
)
from ai.backend.manager.services.deployment.actions.access_token.global_search_access_tokens import (
    GlobalSearchAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.access_token.search_access_tokens import (
    SearchAccessTokensAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.bulk_delete_auto_scaling_rules import (
    BulkDeleteAutoScalingRulesAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.bulk_get_auto_scaling_rules import (
    BulkGetAutoScalingRulesAction,
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
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.global_search_auto_scaling_rules import (
    GlobalSearchAutoScalingRulesAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.search_auto_scaling_rules import (
    SearchAutoScalingRulesAction,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.update_auto_scaling_rule import (
    UpdateAutoScalingRuleAction,
    UpdateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.bulk_get import BulkGetDeploymentsAction
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
    UpsertDeploymentPolicyAction,
    UpsertDeploymentPolicyActionResult,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.bulk_get_deployment_policies import (
    BulkGetDeploymentPoliciesAction,
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
)
from ai.backend.manager.services.deployment.actions.global_search_replicas import (
    GlobalSearchReplicasAction,
)
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupAutoScalingRuleDeploymentAction,
    LookupAutoScalingRuleOwnerAction,
    LookupBulkAutoScalingRuleOwnerAction,
    LookupBulkDeploymentAccessTokenOwnerAction,
    LookupBulkDeploymentPolicyOwnerAction,
    LookupBulkDeploymentRevisionOwnerAction,
    LookupBulkReplicaGroupOwnerAction,
    LookupBulkReplicaOwnerAction,
    LookupDeploymentAccessTokenOwnerAction,
    LookupDeploymentPolicyOwnerAction,
    LookupDeploymentRevisionOwnerAction,
    LookupReplicaGroupOwnerAction,
    LookupReplicaOwnerAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
    AddModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.bulk_get_revisions import (
    BulkGetRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.global_search_revisions import (
    GlobalSearchRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revision_resource_slots import (
    SearchRevisionResourceSlotsAction,
    SearchRevisionResourceSlotsActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.refresh_deployment_revisions import (
    GlobalRefreshDeploymentRevisionsAction,
    GlobalRefreshDeploymentRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.replace_deployment_options import (
    ReplaceDeploymentOptionsAction,
    ReplaceDeploymentOptionsActionResult,
)
from ai.backend.manager.services.deployment.actions.replica.bulk_get_replicas import (
    BulkGetReplicasAction,
)
from ai.backend.manager.services.deployment.actions.replica_group.bulk_get_replica_groups import (
    BulkGetReplicaGroupsAction,
)
from ai.backend.manager.services.deployment.actions.revision_operations import (
    ActivateRevisionAction,
    ActivateRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.route import (
    SearchRoutesAction,
    UpdateRouteTrafficStatusAction,
    UpdateRouteTrafficStatusActionResult,
)
from ai.backend.manager.services.deployment.actions.route.bulk_get_routes import (
    BulkGetRoutesAction,
)
from ai.backend.manager.services.deployment.actions.scoped_search import (
    ScopedSearchDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.search_deployments import (
    GlobalSearchDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.search_legacy_deployments import (
    GlobalSearchLegacyDeploymentsAction,
    GlobalSearchLegacyDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.search_replicas import (
    SearchReplicasAction,
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
        GlobalSearchDeploymentsAction, BatchOpsResult[ModelDeploymentData]
    ]
    # Legacy (REST v1) read variants — full revision. DO NOT USE in new code.
    global_search_legacy: GlobalActionProcessor[
        GlobalSearchLegacyDeploymentsAction, GlobalSearchLegacyDeploymentsActionResult
    ]
    scoped_search: ScopeActionProcessor[
        ScopedSearchDeploymentsAction, ScopedBatchOpsResult[ModelDeploymentData]
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
        SearchDeploymentPoliciesAction, BatchOpsResult[DeploymentPolicyData]
    ]
    upsert_deployment_policy: SingleEntityActionProcessor[
        UpsertDeploymentPolicyAction, UpsertDeploymentPolicyActionResult
    ]

    # Revision operations
    add_model_revision: SingleEntityActionProcessor[
        AddModelRevisionAction, AddModelRevisionActionResult
    ]
    get_revision_by_id: SingleFieldActionProcessor[
        GetRevisionByIdAction, EntityOpsResult[ModelRevisionData]
    ]
    search_revisions: BulkActionProcessor[
        SearchRevisionsAction, ScopedFieldsOpsResult[ModelRevisionData]
    ]
    search_revision_resource_slots: SingleFieldActionProcessor[
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
    search_routes: BulkActionProcessor[SearchRoutesAction, ScopedFieldsOpsResult[RouteInfo]]
    update_route_traffic_status: SingleFieldActionProcessor[
        UpdateRouteTrafficStatusAction, UpdateRouteTrafficStatusActionResult
    ]

    # Replica operations
    get_replica_by_id: SingleFieldActionProcessor[
        GetReplicaByIdAction, EntityOpsResult[ModelReplicaData]
    ]
    search_replicas: BulkActionProcessor[
        SearchReplicasAction, ScopedFieldsOpsResult[ModelReplicaData]
    ]

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
    bulk_delete_auto_scaling_rules: PartialBulkActionProcessor[
        BulkDeleteAutoScalingRulesAction, list[UUID]
    ]
    search_auto_scaling_rules: BulkActionProcessor[
        SearchAutoScalingRulesAction, ScopedFieldsOpsResult[ModelDeploymentAutoScalingRuleData]
    ]
    global_search_auto_scaling_rules: GlobalActionProcessor[
        GlobalSearchAutoScalingRulesAction, BatchOpsResult[ModelDeploymentAutoScalingRuleData]
    ]

    # Access token
    create_access_token: SingleEntityActionProcessor[
        CreateAccessTokenAction, CreateAccessTokenActionResult
    ]
    get_access_token: SingleFieldActionProcessor[
        GetAccessTokenAction, EntityOpsResult[ModelDeploymentAccessTokenData]
    ]
    delete_access_token: SingleFieldActionProcessor[
        DeleteAccessTokenAction, DeleteAccessTokenActionResult
    ]
    bulk_delete_access_tokens: PartialBulkFieldActionProcessor[
        BulkDeleteAccessTokensAction, ModelDeploymentAccessTokenData
    ]
    search_access_tokens: BulkActionProcessor[
        SearchAccessTokensAction, ScopedFieldsOpsResult[ModelDeploymentAccessTokenData]
    ]

    # What the DataLoader reads: checked per deployment.
    bulk_get: PartialBulkActionProcessor[BulkGetDeploymentsAction, ModelDeploymentData]
    # What the DataLoaders read: checked per owning deployment.
    bulk_get_replica_groups: PartialBulkFieldActionProcessor[
        BulkGetReplicaGroupsAction, ReplicaGroupData
    ]
    bulk_get_revisions: PartialBulkFieldActionProcessor[BulkGetRevisionsAction, ModelRevisionData]
    bulk_get_replicas: PartialBulkFieldActionProcessor[BulkGetReplicasAction, ModelReplicaData]
    bulk_get_routes: PartialBulkFieldActionProcessor[BulkGetRoutesAction, RouteInfo]
    bulk_get_access_tokens: PartialBulkFieldActionProcessor[
        BulkGetAccessTokensAction, ModelDeploymentAccessTokenData
    ]
    bulk_get_auto_scaling_rules: PartialBulkFieldActionProcessor[
        BulkGetAutoScalingRulesAction, ModelDeploymentAutoScalingRuleData
    ]
    bulk_get_deployment_policies: BulkActionProcessor[
        BulkGetDeploymentPoliciesAction, OwnedFieldsOpsResult[DeploymentID, DeploymentPolicyData]
    ]

    global_search_replicas: GlobalActionProcessor[
        GlobalSearchReplicasAction, BatchOpsResult[ModelReplicaData]
    ]
    global_search_revisions: GlobalActionProcessor[
        GlobalSearchRevisionsAction, BatchOpsResult[ModelRevisionData]
    ]
    global_search_access_tokens: GlobalActionProcessor[
        GlobalSearchAccessTokensAction, BatchOpsResult[ModelDeploymentAccessTokenData]
    ]

    def __init__(
        self, group: ProcessorGroup[ModelDeploymentData], service: DeploymentService
    ) -> None:
        revisions: LookupFieldGroup[ModelRevisionData] = group.field_group(
            FieldGroupMeta(DeploymentRevisionFieldType()),
            ModelRevisionData,
            LookupDeploymentRevisionOwnerAction,
            LookupBulkDeploymentRevisionOwnerAction,
        )
        replicas: LookupFieldGroup[ModelReplicaData] = group.field_group(
            FieldGroupMeta(ReplicaFieldType()),
            ModelReplicaData,
            LookupReplicaOwnerAction,
            LookupBulkReplicaOwnerAction,
        )
        access_tokens: LookupFieldGroup[ModelDeploymentAccessTokenData] = group.field_group(
            FieldGroupMeta(DeploymentTokenFieldType()),
            ModelDeploymentAccessTokenData,
            LookupDeploymentAccessTokenOwnerAction,
            LookupBulkDeploymentAccessTokenOwnerAction,
        )
        policies: LookupFieldGroup[DeploymentPolicyData] = group.field_group(
            FieldGroupMeta(DeploymentPolicyFieldType()),
            DeploymentPolicyData,
            LookupDeploymentPolicyOwnerAction,
            LookupBulkDeploymentPolicyOwnerAction,
        )
        replica_groups: LookupFieldGroup[ReplicaGroupData] = group.field_group(
            FieldGroupMeta(ReplicaGroupFieldType()),
            ReplicaGroupData,
            LookupReplicaGroupOwnerAction,
            LookupBulkReplicaGroupOwnerAction,
        )
        self.bulk_get = group.partial_bulk_get_ops(BulkGetDeploymentsAction)
        self.bulk_get_replica_groups = replica_groups.partial_bulk_get_ops(
            BulkGetReplicaGroupsAction
        )
        self.bulk_get_revisions = revisions.partial_bulk_get_ops(BulkGetRevisionsAction)
        self.bulk_get_replicas = replicas.partial_bulk_get_ops(BulkGetReplicasAction)
        routes: LookupFieldGroup[RouteInfo] = group.field_group(
            FieldGroupMeta(ReplicaFieldType()),
            RouteInfo,
            LookupReplicaOwnerAction,
            LookupBulkReplicaOwnerAction,
        )
        self.bulk_get_routes = routes.partial_bulk_get_ops(BulkGetRoutesAction)
        self.bulk_get_access_tokens = access_tokens.partial_bulk_get_ops(BulkGetAccessTokensAction)
        auto_scaling_rules: LookupFieldGroup[ModelDeploymentAutoScalingRuleData] = (
            group.field_group(
                FieldGroupMeta(AutoScalingRuleFieldType()),
                ModelDeploymentAutoScalingRuleData,
                LookupAutoScalingRuleOwnerAction,
                LookupBulkAutoScalingRuleOwnerAction,
            )
        )
        self.bulk_get_auto_scaling_rules = auto_scaling_rules.partial_bulk_get_ops(
            BulkGetAutoScalingRulesAction
        )
        self.bulk_get_deployment_policies = policies.atomic_bulk_get_ops(
            BulkGetDeploymentPoliciesAction
        )
        self.lookup_auto_scaling_rule_deployment = group.key_owner_lookup_ops(
            LookupAutoScalingRuleDeploymentAction
        )
        self.global_search_replicas = replicas.global_searcher_ops(GlobalSearchReplicasAction)
        self.global_search_revisions = revisions.global_searcher_ops(GlobalSearchRevisionsAction)
        self.global_search_access_tokens = access_tokens.global_searcher_ops(
            GlobalSearchAccessTokensAction
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
        self.global_search = group.global_searcher_ops(GlobalSearchDeploymentsAction)
        self.global_search_legacy = group.global_scope(
            GlobalSearchLegacyDeploymentsAction, service.search_legacy_deployments
        )
        self.scoped_search = group.scoped_search_ops(ScopedSearchDeploymentsAction)
        self.get_deployment_by_id = group.single_entity(
            GetDeploymentByIdAction, service.get_deployment_by_id
        )
        self.get_legacy_deployment_by_id = group.single_entity(
            GetLegacyDeploymentByIdAction, service.get_legacy_deployment_by_id
        )
        self.get_deployment_policy = group.single_entity(
            GetDeploymentPolicyAction, service.get_deployment_policy
        )
        self.search_deployment_policies = policies.global_searcher_ops(
            SearchDeploymentPoliciesAction
        )
        self.upsert_deployment_policy = group.single_entity(
            UpsertDeploymentPolicyAction, service.upsert_deployment_policy
        )

        # Revision operations
        self.add_model_revision = group.single_entity(
            AddModelRevisionAction, service.add_model_revision
        )
        self.get_revision_by_id = revisions.get_ops(GetRevisionByIdAction)
        self.search_revisions = revisions.atomic_bulk_scoped_search_ops(SearchRevisionsAction)
        self.search_revision_resource_slots = revisions.single_field(
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
        self.search_routes = routes.atomic_bulk_scoped_search_ops(SearchRoutesAction)
        self.update_route_traffic_status = replicas.single_field(
            UpdateRouteTrafficStatusAction, service.update_route_traffic_status
        )

        # Replica operations
        self.get_replica_by_id = replicas.get_ops(GetReplicaByIdAction)
        self.search_replicas = replicas.atomic_bulk_scoped_search_ops(SearchReplicasAction)

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
        self.bulk_delete_auto_scaling_rules = group.partial_bulk(
            BulkDeleteAutoScalingRulesAction, service.bulk_delete_auto_scaling_rules
        )
        self.search_auto_scaling_rules = auto_scaling_rules.atomic_bulk_scoped_search_ops(
            SearchAutoScalingRulesAction
        )
        self.global_search_auto_scaling_rules = auto_scaling_rules.global_searcher_ops(
            GlobalSearchAutoScalingRulesAction
        )

        # Access token
        self.create_access_token = group.single_entity(
            CreateAccessTokenAction, service.create_access_token
        )
        self.get_access_token = access_tokens.get_ops(GetAccessTokenAction)
        self.delete_access_token = access_tokens.single_field(
            DeleteAccessTokenAction, service.delete_access_token
        )
        self.bulk_delete_access_tokens = access_tokens.partial_bulk_field(
            BulkDeleteAccessTokensAction, service.bulk_delete_access_tokens
        )
        self.search_access_tokens = access_tokens.atomic_bulk_scoped_search_ops(
            SearchAccessTokensAction
        )
