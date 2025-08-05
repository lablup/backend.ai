import uuid
from dataclasses import dataclass


@dataclass
class ObjectStorageData:
    id: uuid.UUID
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str
    buckets: list[str]
