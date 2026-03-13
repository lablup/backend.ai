"""Action for creating legacy deployments(Model Service)."""

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import PermissionOperationType, ScopeType
from ai.backend.manager.data.deployment.creator import DeploymentCreationDraft
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)


@dataclass
class CreateLegacyDeploymentAction(DeploymentScopeAction):
    """Action to create a new legacy deployment(Model Service)."""

    draft: DeploymentCreationDraft

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> UUID:
        return self.draft.project_id

    @override
    @classmethod
    def permission_operation_type(cls) -> PermissionOperationType:
        return PermissionOperationType.CREATE


@dataclass
class CreateLegacyDeploymentActionResult(DeploymentScopeActionResult):
    data: DeploymentInfo

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
