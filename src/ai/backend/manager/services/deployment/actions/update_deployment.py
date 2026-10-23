from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.models.endpoint.updaters import DeploymentUpdater
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
)


@dataclass
class UpdateDeploymentAction(DeploymentSingleEntityAction):
    """Action to update an existing deployment."""

    updater: DeploymentUpdater
    # Replaces the designated agents; ``None`` leaves them.
    designated_agents: frozenset[AgentUUID] | None = None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_deployment"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateDeploymentActionResult:
    data: ModelDeploymentData
