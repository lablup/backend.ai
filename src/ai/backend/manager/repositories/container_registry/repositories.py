from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.image.repositories import RepositoryArgs


@dataclass
class ContainerRegistryRepositories:
    repository: ContainerRegistryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ContainerRegistryRepository(args.db)

        return cls(
            repository=repository,
        )
