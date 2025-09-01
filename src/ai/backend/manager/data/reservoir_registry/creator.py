from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator


@dataclass
class ReservoirRegistryCreator(Creator):
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "api_version": self.api_version,
        }
