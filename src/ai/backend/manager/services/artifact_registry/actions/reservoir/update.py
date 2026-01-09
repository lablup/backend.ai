from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryModifierMeta
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class UpdateReservoirRegistryAction(ArtifactRegistryAction):
    updater: Updater[ReservoirRegistryRow]
    meta: ArtifactRegistryModifierMeta

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_reservoir_registry"


@dataclass
class UpdateReservoirRegistryActionResult(BaseActionResult):
    result: ReservoirRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
