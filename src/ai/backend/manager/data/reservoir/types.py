import uuid
from dataclasses import dataclass


@dataclass
class ReservoirData:
    id: uuid.UUID
    name: str
    endpoint: str
