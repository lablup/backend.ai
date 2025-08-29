import uuid
from dataclasses import dataclass


@dataclass
class ObjectStorageNamespaceData:
    id: uuid.UUID
    storage_id: uuid.UUID
    bucket: str
