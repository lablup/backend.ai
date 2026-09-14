"""Action for creating legacy deployments(Model Service)."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.creator import DeploymentCreationDraft
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)


@dataclass
class CreateLegacyDeploymentAction(DeploymentScopeAction):
    """Action to create a new legacy deployment(Model Service)."""

    project_id: ProjectID

    draft: DeploymentCreationDraft

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.project_id,)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_legacy_deployment"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateLegacyDeploymentActionResult(DeploymentScopeActionResult):
    data: DeploymentInfo
