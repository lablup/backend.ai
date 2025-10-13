from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator


@dataclass
class VFSStorageCreator(Creator):
    name: str
    host: str
    base_path: str

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "host": self.host,
            "base_path": self.base_path,
        }
