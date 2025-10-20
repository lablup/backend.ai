import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator


@dataclass
class StorageNamespaceCreator(Creator):
    storage_id: uuid.UUID
    bucket: str

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "storage_id": self.storage_id,
            "namespace": self.bucket,
        }
