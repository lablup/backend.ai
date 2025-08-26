import uuid
from dataclasses import dataclass


@dataclass
class ReservoirRegistryData:
    id: uuid.UUID
    name: str
    endpoint: str
