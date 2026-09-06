from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryModifierMeta
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.reservoir_registry.updaters import ReservoirRegistryUpdater
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistrySingleEntityAction,
)


@dataclass
class UpdateReservoirRegistryAction(ArtifactRegistrySingleEntityAction):
    updater: ReservoirRegistryUpdater
    meta: ArtifactRegistryModifierMeta

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_reservoir_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateReservoirRegistryActionResult:
    result: ReservoirRegistryData
