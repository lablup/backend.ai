import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator


@dataclass
class AssociationArtifactsStoragesCreator(Creator):
    artifact_id: uuid.UUID
    storage_id: uuid.UUID

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "artifact_id": str(self.artifact_id),
            "storage_id": str(self.storage_id),
        }
