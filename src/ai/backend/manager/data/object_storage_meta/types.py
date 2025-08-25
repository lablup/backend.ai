import uuid
from dataclasses import dataclass


@dataclass
class ObjectStorageMetaData:
    id: uuid.UUID
    storage_id: uuid.UUID
    bucket: str
