from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class ListReservoirRegistriesAction(ArtifactRegistryAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_reservoir_registries"


@dataclass
class ListReservoirRegistriesActionResult(BaseActionResult):
    data: list[ReservoirRegistryData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
