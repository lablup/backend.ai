from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator


@dataclass
class ContainerRegistryCreator(Creator):
    """Creator for container registry operations."""

    url: str
    registry_name: str
    project: str
    username: str
    password: str
    type: str = "harbor"
    ssl_verify: bool = True

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "registry_name": self.registry_name,
            "project": self.project,
            "username": self.username,
            "password": self.password,
            "type": self.type,
            "ssl_verify": self.ssl_verify,
        }
