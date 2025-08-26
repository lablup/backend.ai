import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.reservoir.modifier import ReservoirRegistryModifier
from ai.backend.manager.data.reservoir.types import ReservoirRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class UpdateReservoirRegistryAction(ArtifactRegistryAction):
    id: uuid.UUID
    modifier: ReservoirRegistryModifier

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateReservoirRegistryActionResult(BaseActionResult):
    result: ReservoirRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
