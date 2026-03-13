"""Action for creating deployments."""

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import PermissionOperationType, ScopeType
from ai.backend.manager.data.deployment.creator import NewDeploymentCreator
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)


@dataclass
class CreateDeploymentAction(DeploymentScopeAction):
    """Action to create a new deployment(Model Service)."""

    creator: NewDeploymentCreator

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> UUID:
        return self.creator.project_id

    @override
    @classmethod
    def permission_operation_type(cls) -> PermissionOperationType:
        return PermissionOperationType.CREATE


@dataclass
class CreateDeploymentActionResult(DeploymentScopeActionResult):
    data: ModelDeploymentData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
