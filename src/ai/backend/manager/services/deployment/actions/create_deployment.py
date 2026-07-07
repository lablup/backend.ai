"""Action for creating deployments."""

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.creator import NewDeploymentCreator
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.deployment.actions.base import DeploymentScopeAction


@dataclass
class CreateDeploymentAction(DeploymentScopeAction):
    """Action to create a new deployment(Model Service).

    RBAC is enforced against the owner's USER scope (the ``created_user`` on the
    creator metadata), so delegation authorizes the caller against the owner.
    """

    creator: NewDeploymentCreator
    auto_activate: bool

    @override
    def entity_id(self) -> str | None:
        return None  # New deployment doesn't have an ID yet

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.creator.metadata.created_user)

    @override
    def target_element(self) -> RBACElementRef:
        # created_user is the effective owner (the caller, or the delegated
        # owner_id). Authorize the caller against that user's USER scope.
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(self.creator.metadata.created_user),
        )


@dataclass
class CreateDeploymentActionResult(BaseActionResult):
    data: ModelDeploymentData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
