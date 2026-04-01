from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryCreatorMeta
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class CreateReservoirRegistryAction(ArtifactRegistryAction):
    creator: Creator[ReservoirRegistryRow]
    meta: ArtifactRegistryCreatorMeta

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateReservoirActionResult(BaseActionResult):
    result: ReservoirRegistryData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
