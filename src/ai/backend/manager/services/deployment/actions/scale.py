from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import DeploymentInfo, ReplicaSpec
from ai.backend.manager.services.deployment.actions.base import DeploymentAction


@dataclass
class ScaleDeploymentAction(DeploymentAction):
    deployment_id: UUID
    replica_spec: ReplicaSpec

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "scale"


@dataclass
class ScaleDeploymentActionResult(BaseActionResult):
    deployment: DeploymentInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment.id)
