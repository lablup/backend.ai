"""Deployment service processors for GraphQL API."""

from typing import Protocol, override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
    CreateAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.list_access_tokens import (
    ListAccessTokensAction,
    ListAccessTokensActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.batch_load_auto_scaling_rules import (
    BatchLoadAutoScalingRulesAction,
    BatchLoadAutoScalingRulesActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
    CreateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
    DeleteAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.update_auto_scaling_rule import (
    UpdateAutoScalingRuleAction,
    UpdateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.batch_load_deployments import (
    BatchLoadDeploymentsAction,
    BatchLoadDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.batch_load_replicas_by_revision_ids import (
    BatchLoadReplicasByRevisionIdsAction,
    BatchLoadReplicasByRevisionIdsActionResult,
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
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.list_deployments import (
    ListDeploymentsAction,
    ListDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.list_replicas import (
    ListReplicasAction,
    ListReplicasActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
    AddModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.batch_load_revisions import (
    BatchLoadRevisionsAction,
    BatchLoadRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.create_model_revision import (
    CreateModelRevisionAction,
    CreateModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_deployment_id import (
    GetRevisionByDeploymentIdAction,
    GetRevisionByDeploymentIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
    GetRevisionByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_replica_id import (
    GetRevisionByReplicaIdAction,
    GetRevisionByReplicaIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revisions_by_deployment_id import (
    GetRevisionsByDeploymentIdAction,
    GetRevisionsByDeploymentIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.list_revisions import (
    ListRevisionsAction,
    ListRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
    SearchRevisionsActionResult,
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
    SearchDeploymentsAction,
    SearchDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import (
    SyncReplicaAction,
    SyncReplicaActionResult,
)
from ai.backend.manager.services.deployment.actions.update_deployment import (
    UpdateDeploymentAction,
    UpdateDeploymentActionResult,
)


class DeploymentServiceProtocol(Protocol):
    async def create_deployment(
        self, action: CreateDeploymentAction
    ) -> CreateDeploymentActionResult: ...

    async def create_legacy_deployment(
        self, action: CreateLegacyDeploymentAction
    ) -> CreateLegacyDeploymentActionResult: ...

    async def update_deployment(
        self, action: UpdateDeploymentAction
    ) -> UpdateDeploymentActionResult: ...

    async def destroy_deployment(
        self, action: DestroyDeploymentAction
    ) -> DestroyDeploymentActionResult: ...

    async def batch_load_deployments(
        self, action: BatchLoadDeploymentsAction
    ) -> BatchLoadDeploymentsActionResult: ...

    async def create_auto_scaling_rule(
        self, action: CreateAutoScalingRuleAction
    ) -> CreateAutoScalingRuleActionResult: ...

    async def update_auto_scaling_rule(
        self, action: UpdateAutoScalingRuleAction
    ) -> UpdateAutoScalingRuleActionResult: ...

    async def delete_auto_scaling_rule(
        self, action: DeleteAutoScalingRuleAction
    ) -> DeleteAutoScalingRuleActionResult: ...

    async def create_access_token(
        self, action: CreateAccessTokenAction
    ) -> CreateAccessTokenActionResult: ...

    async def sync_replicas(self, action: SyncReplicaAction) -> SyncReplicaActionResult: ...

    async def add_model_revision(
        self, action: AddModelRevisionAction
    ) -> AddModelRevisionActionResult: ...

    async def batch_load_auto_scaling_rules(
        self, action: BatchLoadAutoScalingRulesAction
    ) -> BatchLoadAutoScalingRulesActionResult: ...

    async def get_revision_by_deployment_id(
        self, action: GetRevisionByDeploymentIdAction
    ) -> GetRevisionByDeploymentIdActionResult: ...

    async def get_revision_by_replica_id(
        self, action: GetRevisionByReplicaIdAction
    ) -> GetRevisionByReplicaIdActionResult: ...

    async def get_revision_by_id(
        self, action: GetRevisionByIdAction
    ) -> GetRevisionByIdActionResult: ...

    async def get_revisions_by_deployment_id(
        self, action: GetRevisionsByDeploymentIdAction
    ) -> GetRevisionsByDeploymentIdActionResult: ...

    async def batch_load_replicas_by_revision_ids(
        self, action: BatchLoadReplicasByRevisionIdsAction
    ) -> BatchLoadReplicasByRevisionIdsActionResult: ...

    async def batch_load_revisions(
        self, action: BatchLoadRevisionsAction
    ) -> BatchLoadRevisionsActionResult: ...

    async def list_replicas(self, action: ListReplicasAction) -> ListReplicasActionResult: ...
    async def list_revisions(self, action: ListRevisionsAction) -> ListRevisionsActionResult: ...

    async def create_model_revision(
        self, action: CreateModelRevisionAction
    ) -> CreateModelRevisionActionResult: ...

    async def list_access_tokens(
        self, action: ListAccessTokensAction
    ) -> ListAccessTokensActionResult: ...

    async def get_deployment_policy(
        self, action: GetDeploymentPolicyAction
    ) -> GetDeploymentPolicyActionResult: ...

    async def activate_revision(
        self, action: ActivateRevisionAction
    ) -> ActivateRevisionActionResult: ...

    async def search_routes(self, action: SearchRoutesAction) -> SearchRoutesActionResult: ...

    async def update_route_traffic_status(
        self, action: UpdateRouteTrafficStatusAction
    ) -> UpdateRouteTrafficStatusActionResult: ...

    async def search_deployments(
        self, action: SearchDeploymentsAction
    ) -> SearchDeploymentsActionResult: ...

    async def search_revisions(
        self, action: SearchRevisionsAction
    ) -> SearchRevisionsActionResult: ...


class DeploymentProcessors(AbstractProcessorPackage):
    """Processors for deployment operations."""

    create_deployment: ActionProcessor[CreateDeploymentAction, CreateDeploymentActionResult]
    update_deployment: ActionProcessor[UpdateDeploymentAction, UpdateDeploymentActionResult]
    destroy_deployment: ActionProcessor[DestroyDeploymentAction, DestroyDeploymentActionResult]
    create_legacy_deployment: ActionProcessor[
        CreateLegacyDeploymentAction, CreateLegacyDeploymentActionResult
    ]
    create_auto_scaling_rule: ActionProcessor[
        CreateAutoScalingRuleAction, CreateAutoScalingRuleActionResult
    ]
    update_auto_scaling_rule: ActionProcessor[
        UpdateAutoScalingRuleAction, UpdateAutoScalingRuleActionResult
    ]
    delete_auto_scaling_rule: ActionProcessor[
        DeleteAutoScalingRuleAction, DeleteAutoScalingRuleActionResult
    ]
    create_access_token: ActionProcessor[CreateAccessTokenAction, CreateAccessTokenActionResult]
    list_access_tokens: ActionProcessor[ListAccessTokensAction, ListAccessTokensActionResult]
    sync_replicas: ActionProcessor[SyncReplicaAction, SyncReplicaActionResult]
    add_model_revision: ActionProcessor[AddModelRevisionAction, AddModelRevisionActionResult]
    batch_load_auto_scaling_rules: ActionProcessor[
        BatchLoadAutoScalingRulesAction, BatchLoadAutoScalingRulesActionResult
    ]
    get_revision_by_id: ActionProcessor[GetRevisionByIdAction, GetRevisionByIdActionResult]
    batch_load_revisions: ActionProcessor[BatchLoadRevisionsAction, BatchLoadRevisionsActionResult]
    get_revision_by_deployment_id: ActionProcessor[
        GetRevisionByDeploymentIdAction, GetRevisionByDeploymentIdActionResult
    ]
    get_revision_by_replica_id: ActionProcessor[
        GetRevisionByReplicaIdAction, GetRevisionByReplicaIdActionResult
    ]
    list_deployments: ActionProcessor[ListDeploymentsAction, ListDeploymentsActionResult]
    batch_load_deployments: ActionProcessor[
        BatchLoadDeploymentsAction, BatchLoadDeploymentsActionResult
    ]
    get_revisions_by_deployment_id: ActionProcessor[
        GetRevisionsByDeploymentIdAction, GetRevisionsByDeploymentIdActionResult
    ]
    batch_load_replicas_by_revision_ids: ActionProcessor[
        BatchLoadReplicasByRevisionIdsAction, BatchLoadReplicasByRevisionIdsActionResult
    ]
    list_replicas: ActionProcessor[ListReplicasAction, ListReplicasActionResult]
    list_revisions: ActionProcessor[ListRevisionsAction, ListRevisionsActionResult]
    create_model_revision: ActionProcessor[
        CreateModelRevisionAction, CreateModelRevisionActionResult
    ]
    get_deployment_policy: ActionProcessor[
        GetDeploymentPolicyAction, GetDeploymentPolicyActionResult
    ]
    activate_revision: ActionProcessor[ActivateRevisionAction, ActivateRevisionActionResult]
    search_routes: ActionProcessor[SearchRoutesAction, SearchRoutesActionResult]
    update_route_traffic_status: ActionProcessor[
        UpdateRouteTrafficStatusAction, UpdateRouteTrafficStatusActionResult
    ]
    search_deployments: ActionProcessor[SearchDeploymentsAction, SearchDeploymentsActionResult]
    search_revisions: ActionProcessor[SearchRevisionsAction, SearchRevisionsActionResult]

    def __init__(
        self, service: DeploymentServiceProtocol, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_auto_scaling_rule = ActionProcessor(
            service.create_auto_scaling_rule, action_monitors
        )
        self.update_auto_scaling_rule = ActionProcessor(
            service.update_auto_scaling_rule, action_monitors
        )
        self.delete_auto_scaling_rule = ActionProcessor(
            service.delete_auto_scaling_rule, action_monitors
        )
        self.batch_load_deployments = ActionProcessor(
            service.batch_load_deployments, action_monitors
        )
        self.create_deployment = ActionProcessor(service.create_deployment, action_monitors)
        self.destroy_deployment = ActionProcessor(service.destroy_deployment, action_monitors)
        self.update_deployment = ActionProcessor(service.update_deployment, action_monitors)
        self.create_legacy_deployment = ActionProcessor(
            service.create_legacy_deployment, action_monitors
        )
        self.create_access_token = ActionProcessor(service.create_access_token, action_monitors)
        self.list_access_tokens = ActionProcessor(service.list_access_tokens, action_monitors)
        self.sync_replicas = ActionProcessor(service.sync_replicas, action_monitors)
        self.add_model_revision = ActionProcessor(service.add_model_revision, action_monitors)
        self.batch_load_auto_scaling_rules = ActionProcessor(
            service.batch_load_auto_scaling_rules, action_monitors
        )
        self.get_revision_by_replica_id = ActionProcessor(
            service.get_revision_by_replica_id, action_monitors
        )
        self.get_revision_by_id = ActionProcessor(service.get_revision_by_id, action_monitors)
        self.get_revisions_by_deployment_id = ActionProcessor(
            service.get_revisions_by_deployment_id, action_monitors
        )
        self.batch_load_replicas_by_revision_ids = ActionProcessor(
            service.batch_load_replicas_by_revision_ids, action_monitors
        )
        self.list_replicas = ActionProcessor(service.list_replicas, action_monitors)
        self.list_revisions = ActionProcessor(service.list_revisions, action_monitors)
        self.create_model_revision = ActionProcessor(service.create_model_revision, action_monitors)
        self.batch_load_revisions = ActionProcessor(service.batch_load_revisions, action_monitors)
        self.get_deployment_policy = ActionProcessor(service.get_deployment_policy, action_monitors)
        self.activate_revision = ActionProcessor(service.activate_revision, action_monitors)
        self.search_routes = ActionProcessor(service.search_routes, action_monitors)
        self.update_route_traffic_status = ActionProcessor(
            service.update_route_traffic_status, action_monitors
        )
        self.search_deployments = ActionProcessor(service.search_deployments, action_monitors)
        self.search_revisions = ActionProcessor(service.search_revisions, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateDeploymentAction.spec(),
            DestroyDeploymentAction.spec(),
            CreateAutoScalingRuleAction.spec(),
            UpdateAutoScalingRuleAction.spec(),
            UpdateDeploymentAction.spec(),
            DeleteAutoScalingRuleAction.spec(),
            CreateAccessTokenAction.spec(),
            SyncReplicaAction.spec(),
            AddModelRevisionAction.spec(),
            BatchLoadAutoScalingRulesAction.spec(),
            GetRevisionByDeploymentIdAction.spec(),
            GetRevisionByReplicaIdAction.spec(),
            GetRevisionByIdAction.spec(),
            GetRevisionsByDeploymentIdAction.spec(),
            ListRevisionsAction.spec(),
            ListReplicasAction.spec(),
            CreateLegacyDeploymentAction.spec(),
            CreateModelRevisionAction.spec(),
            BatchLoadRevisionsAction.spec(),
            BatchLoadDeploymentsAction.spec(),
            ListAccessTokensAction.spec(),
            BatchLoadReplicasByRevisionIdsAction.spec(),
            GetDeploymentPolicyAction.spec(),
            ActivateRevisionAction.spec(),
            SearchRoutesAction.spec(),
            UpdateRouteTrafficStatusAction.spec(),
            SearchDeploymentsAction.spec(),
            SearchRevisionsAction.spec(),
        ]
