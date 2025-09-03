import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetReservoirRegistryAction(ArtifactRegistryAction):
    reservoir_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.reservoir_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_reservoir_registry"


@dataclass
class GetReservoirRegistryActionResult(BaseActionResult):
    result: ReservoirRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
