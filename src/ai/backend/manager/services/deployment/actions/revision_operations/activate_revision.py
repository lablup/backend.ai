"""Action for activating a deployment revision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelDeploymentData

from .base import RevisionOperationBaseAction


@dataclass
class ActivateRevisionAction(RevisionOperationBaseAction):
    """Action to activate a specific revision to be the current revision."""

    deployment_id: UUID
    revision_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.revision_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "activate"


@dataclass
class ActivateRevisionActionResult(BaseActionResult):
    """Result of activating a revision."""

    deployment: ModelDeploymentData
    previous_revision_id: Optional[UUID]
    activated_revision_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.activated_revision_id)
