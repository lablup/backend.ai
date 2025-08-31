import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class DeleteReservoirRegistryAction(ArtifactRegistryAction):
    reservoir_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.reservoir_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_reservoir_registry"


@dataclass
class DeleteReservoirActionResult(BaseActionResult):
    deleted_reservoir_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deleted_reservoir_id)
