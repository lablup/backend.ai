"""Action for destroying deployments."""

import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class DestroyDeploymentAction(DeploymentBaseAction):
    """Action to destroy an existing deployment."""

    endpoint_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.endpoint_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "destroy"


@dataclass
class DestroyDeploymentActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
