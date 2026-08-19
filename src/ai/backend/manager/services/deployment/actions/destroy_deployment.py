"""Action for destroying deployments."""

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
)


@dataclass
class DestroyDeploymentAction(DeploymentSingleEntityAction):
    """Action to destroy an existing deployment."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "destroy_deployment"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DestroyDeploymentActionResult:
    success: bool
