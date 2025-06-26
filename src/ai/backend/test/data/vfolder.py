import uuid
from dataclasses import dataclass


@dataclass
class VFolderMeta:
    id: uuid.UUID
    name: str
