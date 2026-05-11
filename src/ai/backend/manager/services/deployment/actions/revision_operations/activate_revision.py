"""Action for activating a deployment revision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentPolicyData, ModelDeploymentData

from .base import RevisionOperationBaseAction


@dataclass
class ActivateRevisionAction(RevisionOperationBaseAction):
    """Action to activate a specific revision to be the current revision."""

    deployment_id: DeploymentID
    revision_id: DeploymentRevisionID

    @override
    def entity_id(self) -> str | None:
        return str(self.revision_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ActivateRevisionActionResult(BaseActionResult):
    """Result of activating a revision."""

    deployment: ModelDeploymentData
    previous_revision_id: DeploymentRevisionID | None
    activated_revision_id: DeploymentRevisionID
    deployment_policy: DeploymentPolicyData

    @override
    def entity_id(self) -> str | None:
        return str(self.activated_revision_id)
