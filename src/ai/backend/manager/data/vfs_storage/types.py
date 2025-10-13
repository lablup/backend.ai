import uuid
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dto.manager.response import VFSStorageResponse


@dataclass
class VFSStorageData:
    id: uuid.UUID
    name: str
    host: str
    base_path: Path

    def to_dto(self) -> VFSStorageResponse:
        return VFSStorageResponse(
            id=str(self.id),
            name=self.name,
            host=self.host,
            base_path=str(self.base_path),
        )
