from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class ListReservoirRegistriesAction(ArtifactRegistryAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_reservoir_registries"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListReservoirRegistriesActionResult:
    data: list[ReservoirRegistryData]
