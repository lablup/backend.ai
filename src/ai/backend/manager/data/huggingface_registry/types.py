import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class HuggingFaceRegistryData:
    id: uuid.UUID
    url: str
    name: str
    token: Optional[str]
