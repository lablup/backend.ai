import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetReservoirRegistryAction(ArtifactRegistryAction):
    reservoir_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.reservoir_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetReservoirRegistryActionResult(BaseActionResult):
    result: ReservoirRegistryData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
