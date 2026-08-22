import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetReservoirRegistriesAction(ArtifactRegistryAction):
    registry_ids: list[uuid.UUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_reservoir_registries"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetReservoirRegistriesActionResult:
    result: list[ReservoirRegistryData]
