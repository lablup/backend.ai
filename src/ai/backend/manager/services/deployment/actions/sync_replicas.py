from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.replica.base import DeploymentReplicaBaseAction


@dataclass
class SyncReplicaAction(DeploymentReplicaBaseAction):
    """Action to sync replicas for an existing deployment."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "sync_replica"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class SyncReplicaActionResult:
    success: bool
