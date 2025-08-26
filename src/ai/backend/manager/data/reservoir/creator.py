from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator


@dataclass
class ReservoirCreator(Creator):
    name: str
    endpoint: str

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "endpoint": self.endpoint,
        }
