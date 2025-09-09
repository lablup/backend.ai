from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class GetReplicasByRevisionIdAction(DeploymentBaseAction):
    revision_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.revision_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_replicas_by_revision_id"


@dataclass
class GetReplicasByRevisionIdActionResult(BaseActionResult):
    data: list[ModelReplicaData]

    @override
    def entity_id(self) -> Optional[str]:
        return None  # This is a list operation for replicas
