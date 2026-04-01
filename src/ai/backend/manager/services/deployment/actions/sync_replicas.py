from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.replica.base import DeploymentReplicaBaseAction


@dataclass
class SyncReplicaAction(DeploymentReplicaBaseAction):
    """Action to sync replicas for an existing deployment."""

    deployment_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class SyncReplicaActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
