from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.services.deployment.actions.base import DeploymentAction


@dataclass
class ListDeploymentsAction(DeploymentAction):
    session_owner_id: UUID
    name: Optional[str] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"


@dataclass
class ListDeploymentsActionResult(BaseActionResult):
    deployments: list[DeploymentInfo]

    @override
    def entity_id(self) -> Optional[str]:
        return None
