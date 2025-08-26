from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.reservoir.types import ReservoirData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class ListReservoirRegistriesAction(ArtifactRegistryAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"


@dataclass
class ListReservoirRegistriesActionResult(BaseActionResult):
    data: list[ReservoirData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
