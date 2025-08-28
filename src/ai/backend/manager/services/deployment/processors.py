"""Deployment service processors for GraphQL API."""

from typing import Protocol, override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import (
    SyncReplicaAction,
    SyncReplicaActionResult,
)


class DeploymentServiceProtocol(Protocol):
    async def create(self, action: CreateDeploymentAction) -> CreateDeploymentActionResult: ...

    async def destroy(self, action: DestroyDeploymentAction) -> DestroyDeploymentActionResult: ...

    async def sync_replicas(self, action: SyncReplicaAction) -> SyncReplicaActionResult: ...


class DeploymentProcessors(AbstractProcessorPackage):
    """Processors for deployment operations."""

    create_deployment: ActionProcessor[CreateDeploymentAction, CreateDeploymentActionResult]
    destroy_deployment: ActionProcessor[DestroyDeploymentAction, DestroyDeploymentActionResult]
    sync_replicas: ActionProcessor[SyncReplicaAction, SyncReplicaActionResult]

    def __init__(
        self, service: DeploymentServiceProtocol, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_deployment = ActionProcessor(service.create, action_monitors)
        self.destroy_deployment = ActionProcessor(service.destroy, action_monitors)
        self.sync_replicas = ActionProcessor(service.sync_replicas, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateDeploymentAction.spec(),
            DestroyDeploymentAction.spec(),
            SyncReplicaAction.spec(),
        ]
