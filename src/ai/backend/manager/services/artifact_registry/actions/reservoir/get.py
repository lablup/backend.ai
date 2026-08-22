import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistrySingleEntityAction,
)


@dataclass
class GetReservoirRegistryAction(ArtifactRegistrySingleEntityAction):
    reservoir_id: uuid.UUID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_reservoir_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetReservoirRegistryActionResult:
    result: ReservoirRegistryData
