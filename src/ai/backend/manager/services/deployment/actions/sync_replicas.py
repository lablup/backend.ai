from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class SyncReplicaAction(DeploymentBaseAction):
    """Action to sync replicas for an existing deployment."""

    deployment_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "sync_replicas"


@dataclass
class SyncReplicaActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
