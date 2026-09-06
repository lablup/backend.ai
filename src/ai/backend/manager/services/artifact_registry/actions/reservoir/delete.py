import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistrySingleEntityAction,
)


@dataclass
class DeleteReservoirRegistryAction(ArtifactRegistrySingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_reservoir_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteReservoirActionResult:
    deleted_reservoir_id: uuid.UUID
