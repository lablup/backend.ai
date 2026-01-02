"""Action for getting deployment policy."""

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.deployment_policy import DeploymentPolicyData
from ai.backend.manager.services.deployment.actions.deployment_policy.base import (
    DeploymentPolicyBaseAction,
)


@dataclass
class GetDeploymentPolicyAction(DeploymentPolicyBaseAction):
    """Action to get a deployment policy by endpoint ID."""

    endpoint_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.endpoint_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetDeploymentPolicyActionResult(BaseActionResult):
    """Result of getting a deployment policy."""

    data: DeploymentPolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
