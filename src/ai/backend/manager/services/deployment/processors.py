"""Deployment service processors for GraphQL API."""

from typing import Protocol, override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.deployment.actions.create_auto_scaling_rule import (
    CreateAutoScalingRuleAction,
    CreateAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.list_deployments import (
    ListDeploymentsAction,
    ListDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.list_model_revisions import (
    ListModelRevisionsAction,
    ListModelRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.list_replicas import (
    ListModelReplicasAction,
    ListModelReplicasActionResult,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import (
    SyncReplicaAction,
    SyncReplicaActionResult,
)


class DeploymentServiceProtocol(Protocol):
    async def list_model_replicas(
        self, action: ListModelReplicasAction
    ) -> ListModelReplicasActionResult: ...

    async def list_model_revisions(
        self, action: ListModelRevisionsAction
    ) -> ListModelRevisionsActionResult: ...

    async def list_deployments(
        self, action: ListDeploymentsAction
    ) -> ListDeploymentsActionResult: ...

    async def create(self, action: CreateDeploymentAction) -> CreateDeploymentActionResult: ...

    async def destroy(self, action: DestroyDeploymentAction) -> DestroyDeploymentActionResult: ...

    async def sync_replicas(self, action: SyncReplicaAction) -> SyncReplicaActionResult: ...

    async def create_auto_scaling_rule(
        self, action: CreateAutoScalingRuleAction
    ) -> CreateAutoScalingRuleActionResult: ...


class DeploymentProcessors(AbstractProcessorPackage):
    """Processors for deployment operations."""

    list_deployments: ActionProcessor[ListDeploymentsAction, ListDeploymentsActionResult]
    list_model_revisions: ActionProcessor[ListModelRevisionsAction, ListModelRevisionsActionResult]
    list_model_replicas: ActionProcessor[ListModelReplicasAction, ListModelReplicasActionResult]
    create_deployment: ActionProcessor[CreateDeploymentAction, CreateDeploymentActionResult]
    destroy_deployment: ActionProcessor[DestroyDeploymentAction, DestroyDeploymentActionResult]
    sync_replicas: ActionProcessor[SyncReplicaAction, SyncReplicaActionResult]
    create_auto_scaling_rule: ActionProcessor[
        CreateAutoScalingRuleAction, CreateAutoScalingRuleActionResult
    ]

    def __init__(
        self, service: DeploymentServiceProtocol, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_auto_scaling_rule = ActionProcessor(
            service.create_auto_scaling_rule, action_monitors
        )
        self.list_deployments = ActionProcessor(service.list_deployments, action_monitors)
        self.list_model_revisions = ActionProcessor(service.list_model_revisions, action_monitors)
        self.list_model_replicas = ActionProcessor(service.list_model_replicas, action_monitors)
        self.create_deployment = ActionProcessor(service.create, action_monitors)
        self.destroy_deployment = ActionProcessor(service.destroy, action_monitors)
        self.sync_replicas = ActionProcessor(service.sync_replicas, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateDeploymentAction.spec(),
            DestroyDeploymentAction.spec(),
            SyncReplicaAction.spec(),
            CreateAutoScalingRuleAction.spec(),
        ]
