"""Action for destroying deployments."""

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class DestroyDeploymentAction(DeploymentBaseAction):
    """Action to destroy an existing deployment."""

    endpoint_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.endpoint_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DestroyDeploymentActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
