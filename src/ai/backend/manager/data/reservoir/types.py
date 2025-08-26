import uuid
from dataclasses import dataclass


@dataclass
class ReservoirRegistryData:
    id: uuid.UUID
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str
