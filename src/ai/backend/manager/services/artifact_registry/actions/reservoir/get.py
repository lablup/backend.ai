import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.reservoir.types import ReservoirData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetReservoirAction(ArtifactRegistryAction):
    reservoir_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.reservoir_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetReservoirActionResult(BaseActionResult):
    result: ReservoirData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
