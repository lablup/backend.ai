import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VFSStorageData:
    id: uuid.UUID
    name: str
    host: str
    base_path: Path
