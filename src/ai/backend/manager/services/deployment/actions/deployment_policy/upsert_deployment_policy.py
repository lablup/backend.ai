"""Action for upserting a deployment policy."""

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.data.deployment.upserter import DeploymentPolicyUpserter
from ai.backend.manager.services.deployment.actions.deployment_policy.base import (
    DeploymentPolicyBaseAction,
)


@dataclass
class UpsertDeploymentPolicyAction(DeploymentPolicyBaseAction):
    """Action to create or update a deployment policy using ON CONFLICT."""

    upserter: DeploymentPolicyUpserter

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upsert_deployment_policy"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpsertDeploymentPolicyActionResult:
    """Result of upserting a deployment policy."""

    data: DeploymentPolicyData
    created: bool
