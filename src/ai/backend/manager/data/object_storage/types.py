import uuid
from dataclasses import dataclass


@dataclass
class ObjectStorageData:
    id: uuid.UUID
    access_key: str
    secret_key: str
    endpoint: str
    region: str
    buckets: list[str]
