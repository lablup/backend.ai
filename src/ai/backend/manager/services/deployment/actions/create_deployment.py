"""Action for creating deployments."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.creator import NewDeploymentCreator
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)


@dataclass
class CreateDeploymentAction(DeploymentScopeAction):
    """Action to create a new deployment(Model Service)."""

    project_id: ProjectID

    creator: NewDeploymentCreator
    auto_activate: bool

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.project_id,)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_deployment"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateDeploymentActionResult(DeploymentScopeActionResult):
    data: ModelDeploymentData
