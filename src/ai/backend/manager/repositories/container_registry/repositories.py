from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.container_registry.db_source.db_source import (
    ContainerRegistryDBSource,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ContainerRegistryRepositories:
    repository: ContainerRegistryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        db_source = ContainerRegistryDBSource(args.db)
        return cls(repository=ContainerRegistryRepository(db_source))
