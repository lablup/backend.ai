import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.types import Creator


# TODO: Check if we need to this
@dataclass
class ArtifactRegistryCreator(Creator):
    registry_id: uuid.UUID
    name: str
    type: ArtifactRegistryType

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {"name": self.name, "type": self.type.value, "registry_id": self.registry_id}
