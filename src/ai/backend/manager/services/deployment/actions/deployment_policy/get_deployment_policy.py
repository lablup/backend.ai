"""Action for getting deployment policy."""

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.services.deployment.actions.deployment_policy.base import (
    DeploymentPolicyBaseAction,
)


@dataclass
class GetDeploymentPolicyAction(DeploymentPolicyBaseAction):
    """Action to get a deployment policy by deployment ID."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_deployment_policy"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetDeploymentPolicyActionResult:
    """Result of getting a deployment policy."""

    data: DeploymentPolicyData
