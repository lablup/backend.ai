import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.reservoir.modifier import ReservoirModifier
from ai.backend.manager.data.reservoir.types import ReservoirData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class UpdateReservoirRegistryAction(ArtifactRegistryAction):
    id: uuid.UUID
    modifier: ReservoirModifier

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateReservoirRegistryActionResult(BaseActionResult):
    result: ReservoirData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
