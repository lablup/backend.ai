"""Action for creating legacy deployments(Model Service)."""

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.creator import DeploymentCreationDraft
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class CreateLegacyDeploymentAction(DeploymentBaseAction):
    """Action to create a new legacy deployment(Model Service)."""

    draft: DeploymentCreationDraft

    @override
    def entity_id(self) -> Optional[str]:
        return None  # New deployment doesn't have an ID yet

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateLegacyDeploymentActionResult(BaseActionResult):
    data: DeploymentInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
