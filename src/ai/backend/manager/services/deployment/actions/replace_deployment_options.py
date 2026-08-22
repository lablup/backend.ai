from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentOptions
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
)


@dataclass
class ReplaceDeploymentOptionsAction(DeploymentSingleEntityAction):
    """Action to fully replace the ``options`` surface of a deployment.

    Uses the same RBAC scope as ``UpdateDeploymentAction`` so a regular
    user can replace options on their own deployment.
    """

    options: DeploymentOptions

    @override
    @classmethod
    def action_name(cls) -> str:
        return "replace_deployment_options"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ReplaceDeploymentOptionsActionResult:
    """Result of replacing a deployment's ``options`` surface.

    Carries only the refreshed :class:`DeploymentOptions` — callers that
    need the surrounding deployment node are expected to re-fetch it.
    """

    options: DeploymentOptions
