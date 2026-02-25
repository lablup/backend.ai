"""Action for updating a deployment policy."""

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.deployment.actions.deployment_policy.base import (
    DeploymentPolicyBaseAction,
)


@dataclass
class UpdateDeploymentPolicyAction(DeploymentPolicyBaseAction):
    """Action to update a deployment policy."""

    policy_id: UUID
    updater: Updater[DeploymentPolicyRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.policy_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateDeploymentPolicyActionResult(BaseActionResult):
    """Result of updating a deployment policy."""

    data: DeploymentPolicyData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
