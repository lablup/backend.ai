import uuid
from dataclasses import dataclass


@dataclass
class StorageNamespaceData:
    id: uuid.UUID
    storage_id: uuid.UUID
    namespace: str
