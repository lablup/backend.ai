"""Action for creating legacy deployments(Model Service)."""

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import OperationType, RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.creator import DeploymentCreationDraft
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)


@dataclass
class CreateLegacyDeploymentAction(DeploymentScopeAction):
    """Action to create a new legacy deployment(Model Service)."""

    draft: DeploymentCreationDraft

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.draft.metadata.project)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.draft.metadata.project))


@dataclass
class CreateLegacyDeploymentActionResult(DeploymentScopeActionResult):
    data: DeploymentInfo

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.data.project_id)
