"""Deployment service processors for GraphQL API."""

from typing import TYPE_CHECKING, override

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

if TYPE_CHECKING:
    from ai.backend.manager.services.deployment.service import DeploymentService


class DeploymentProcessors(AbstractProcessorPackage):
    """Processors for deployment operations."""

    create_deployment: ActionProcessor[CreateDeploymentAction, CreateDeploymentActionResult]
    destroy_deployment: ActionProcessor[DestroyDeploymentAction, DestroyDeploymentActionResult]

    def __init__(self, service: "DeploymentService", action_monitors: list[ActionMonitor]) -> None:
        self.create_deployment = ActionProcessor(service.create, action_monitors)
        self.destroy_deployment = ActionProcessor(service.destroy, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateDeploymentAction.spec(),
            DestroyDeploymentAction.spec(),
        ]
