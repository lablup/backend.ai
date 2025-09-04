import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class HuggingFaceRegistryData:
    id: uuid.UUID
    name: str
    url: str
    token: Optional[str]
