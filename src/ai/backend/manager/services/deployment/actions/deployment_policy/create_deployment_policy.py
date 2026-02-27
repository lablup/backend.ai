"""Action for creating a deployment policy."""

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.creator import DeploymentPolicyCreator
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.services.deployment.actions.deployment_policy.base import (
    DeploymentPolicyBaseAction,
)


@dataclass
class CreateDeploymentPolicyAction(DeploymentPolicyBaseAction):
    """Action to create a deployment policy for a deployment."""

    creator: DeploymentPolicyCreator

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateDeploymentPolicyActionResult(BaseActionResult):
    """Result of creating a deployment policy."""

    data: DeploymentPolicyData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
