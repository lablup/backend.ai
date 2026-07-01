from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentOptions
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
    DeploymentSingleEntityActionResult,
)


@dataclass
class ReplaceDeploymentOptionsAction(DeploymentSingleEntityAction):
    """Action to fully replace the ``options`` surface of a deployment.

    Uses the same RBAC scope as ``UpdateDeploymentAction`` so a regular
    user can replace options on their own deployment.
    """

    deployment_id: DeploymentID
    options: DeploymentOptions

    @override
    def target_entity_id(self) -> str:
        return str(self.deployment_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.MODEL_DEPLOYMENT, str(self.deployment_id))

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ReplaceDeploymentOptionsActionResult(DeploymentSingleEntityActionResult):
    """Result of replacing a deployment's ``options`` surface.

    Carries only the refreshed :class:`DeploymentOptions` — callers that
    need the surrounding deployment node are expected to re-fetch it.
    """

    deployment_id: DeploymentID
    options: DeploymentOptions

    @override
    def target_entity_id(self) -> str:
        return str(self.deployment_id)
