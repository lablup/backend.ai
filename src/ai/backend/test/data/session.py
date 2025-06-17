import uuid
from dataclasses import dataclass


@dataclass
class CreatedSessionMeta:
    id: uuid.UUID
    name: str
