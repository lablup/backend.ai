from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.types import Creator


@dataclass
class HuggingFaceRegistryCreator(Creator):
    name: str
    url: str
    token: Optional[str]

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "token": self.token,
        }
