from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.types import Creator


@dataclass
class HuggingFaceRegistryCreator(Creator):
    url: str
    token: Optional[str]

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "token": self.token,
        }
