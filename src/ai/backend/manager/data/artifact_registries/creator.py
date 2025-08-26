import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator


@dataclass
class ArtifactRegistryCreator(Creator):
    registry_id: uuid.UUID
    name: str
    type: str

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {"name": self.name, "type": self.type, "registry_id": self.registry_id}
