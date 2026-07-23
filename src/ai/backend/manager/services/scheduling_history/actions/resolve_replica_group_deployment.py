from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import SchedulingHistoryAction


@dataclass
class ResolveReplicaGroupDeploymentAction(SchedulingHistoryAction):
    """Resolve the deployment owning a replica group.

    Pre-step for a replica-group-only scope: the owning deployment is the
    authorization subject, so the caller resolves it first and passes it to the
    scoped action.
    """

    replica_group_id: ReplicaGroupID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.MODEL_DEPLOYMENT

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.replica_group_id)


@dataclass
class ResolveReplicaGroupDeploymentActionResult(BaseActionResult):
    """Result of resolving the deployment owning a replica group."""

    deployment_id: DeploymentID

    @override
    def entity_id(self) -> str | None:
        return str(self.deployment_id)
