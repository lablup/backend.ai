from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator


@dataclass
class ObjectStorageCreator(Creator):
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "host": self.host,
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "endpoint": self.endpoint,
            "region": self.region,
        }
