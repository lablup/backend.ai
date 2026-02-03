"""Deployment service processors for GraphQL API."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
    CreateAccessTokenActionResult,
)
from ai.backend.manager.services.deployment.actions.access_token.search_access_tokens import (
    SearchAccessTokensAction,
    SearchAccessTokensActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
    CreateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.delete_auto_scaling_rule import (
    DeleteAutoScalingRuleAction,
    DeleteAutoScalingRuleActionResult,
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
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.get_deployment_by_id import (
    GetDeploymentByIdAction,
    GetDeploymentByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.get_replica_by_id import (
    GetReplicaByIdAction,
    GetReplicaByIdActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
    AddModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.create_model_revision import (
    CreateModelRevisionAction,
    CreateModelRevisionActionResult,
)
from ai.backend.manager.services.deployment.actions.model_revision.get_revision_by_id import (
    GetRevisionByIdAction,
    GetRevisionByIdActionResult,
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


class DeploymentProcessors(AbstractProcessorPackage):
    """Processors for deployment operations."""

    # Deployment CRUD
    create_deployment: ActionProcessor[CreateDeploymentAction, CreateDeploymentActionResult]
    create_legacy_deployment: ActionProcessor[
        CreateLegacyDeploymentAction, CreateLegacyDeploymentActionResult
    ]
    update_deployment: ActionProcessor[UpdateDeploymentAction, UpdateDeploymentActionResult]
    destroy_deployment: ActionProcessor[DestroyDeploymentAction, DestroyDeploymentActionResult]
    search_deployments: ActionProcessor[SearchDeploymentsAction, SearchDeploymentsActionResult]
    get_deployment_by_id: ActionProcessor[GetDeploymentByIdAction, GetDeploymentByIdActionResult]
    get_deployment_policy: ActionProcessor[
        GetDeploymentPolicyAction, GetDeploymentPolicyActionResult
    ]

    # Revision operations
    create_model_revision: ActionProcessor[
        CreateModelRevisionAction, CreateModelRevisionActionResult
    ]
    add_model_revision: ActionProcessor[AddModelRevisionAction, AddModelRevisionActionResult]
    get_revision_by_id: ActionProcessor[GetRevisionByIdAction, GetRevisionByIdActionResult]
    search_revisions: ActionProcessor[SearchRevisionsAction, SearchRevisionsActionResult]
    activate_revision: ActionProcessor[ActivateRevisionAction, ActivateRevisionActionResult]

    # Route operations
    sync_replicas: ActionProcessor[SyncReplicaAction, SyncReplicaActionResult]
    search_routes: ActionProcessor[SearchRoutesAction, SearchRoutesActionResult]
    update_route_traffic_status: ActionProcessor[
        UpdateRouteTrafficStatusAction, UpdateRouteTrafficStatusActionResult
    ]

    # Replica operations
    get_replica_by_id: ActionProcessor[GetReplicaByIdAction, GetReplicaByIdActionResult]
    search_replicas: ActionProcessor[SearchReplicasAction, SearchReplicasActionResult]

    # Auto-scaling rules
    create_auto_scaling_rule: ActionProcessor[
        CreateAutoScalingRuleAction, CreateAutoScalingRuleActionResult
    ]
    update_auto_scaling_rule: ActionProcessor[
        UpdateAutoScalingRuleAction, UpdateAutoScalingRuleActionResult
    ]
    delete_auto_scaling_rule: ActionProcessor[
        DeleteAutoScalingRuleAction, DeleteAutoScalingRuleActionResult
    ]
    search_auto_scaling_rules: ActionProcessor[
        SearchAutoScalingRulesAction, SearchAutoScalingRulesActionResult
    ]

    # Access token
    create_access_token: ActionProcessor[CreateAccessTokenAction, CreateAccessTokenActionResult]
    search_access_tokens: ActionProcessor[SearchAccessTokensAction, SearchAccessTokensActionResult]

    def __init__(self, service: DeploymentService, action_monitors: list[ActionMonitor]) -> None:
        # Deployment CRUD
        self.create_deployment = ActionProcessor(service.create_deployment, action_monitors)
        self.create_legacy_deployment = ActionProcessor(
            service.create_legacy_deployment, action_monitors
        )
        self.update_deployment = ActionProcessor(service.update_deployment, action_monitors)
        self.destroy_deployment = ActionProcessor(service.destroy_deployment, action_monitors)
        self.search_deployments = ActionProcessor(service.search_deployments, action_monitors)
        self.get_deployment_by_id = ActionProcessor(service.get_deployment_by_id, action_monitors)
        self.get_deployment_policy = ActionProcessor(service.get_deployment_policy, action_monitors)

        # Revision operations
        self.create_model_revision = ActionProcessor(service.create_model_revision, action_monitors)
        self.add_model_revision = ActionProcessor(service.add_model_revision, action_monitors)
        self.get_revision_by_id = ActionProcessor(service.get_revision_by_id, action_monitors)
        self.search_revisions = ActionProcessor(service.search_revisions, action_monitors)
        self.activate_revision = ActionProcessor(service.activate_revision, action_monitors)

        # Route operations
        self.sync_replicas = ActionProcessor(service.sync_replicas, action_monitors)
        self.search_routes = ActionProcessor(service.search_routes, action_monitors)
        self.update_route_traffic_status = ActionProcessor(
            service.update_route_traffic_status, action_monitors
        )

        # Replica operations
        self.get_replica_by_id = ActionProcessor(service.get_replica_by_id, action_monitors)
        self.search_replicas = ActionProcessor(service.search_replicas, action_monitors)

        # Auto-scaling rules
        self.create_auto_scaling_rule = ActionProcessor(
            service.create_auto_scaling_rule, action_monitors
        )
        self.update_auto_scaling_rule = ActionProcessor(
            service.update_auto_scaling_rule, action_monitors
        )
        self.delete_auto_scaling_rule = ActionProcessor(
            service.delete_auto_scaling_rule, action_monitors
        )
        self.search_auto_scaling_rules = ActionProcessor(
            service.search_auto_scaling_rules, action_monitors
        )

        # Access token
        self.create_access_token = ActionProcessor(service.create_access_token, action_monitors)
        self.search_access_tokens = ActionProcessor(service.search_access_tokens, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            # Deployment CRUD
            CreateDeploymentAction.spec(),
            CreateLegacyDeploymentAction.spec(),
            UpdateDeploymentAction.spec(),
            DestroyDeploymentAction.spec(),
            SearchDeploymentsAction.spec(),
            GetDeploymentByIdAction.spec(),
            GetDeploymentPolicyAction.spec(),
            # Revision operations
            CreateModelRevisionAction.spec(),
            AddModelRevisionAction.spec(),
            GetRevisionByIdAction.spec(),
            SearchRevisionsAction.spec(),
            ActivateRevisionAction.spec(),
            # Route operations
            SyncReplicaAction.spec(),
            SearchRoutesAction.spec(),
            UpdateRouteTrafficStatusAction.spec(),
            # Replica operations
            GetReplicaByIdAction.spec(),
            SearchReplicasAction.spec(),
            # Auto-scaling rules
            CreateAutoScalingRuleAction.spec(),
            UpdateAutoScalingRuleAction.spec(),
            DeleteAutoScalingRuleAction.spec(),
            SearchAutoScalingRulesAction.spec(),
            # Access token
            CreateAccessTokenAction.spec(),
            SearchAccessTokensAction.spec(),
        ]
