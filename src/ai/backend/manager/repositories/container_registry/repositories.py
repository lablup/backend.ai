from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ContainerRegistryRepositories:
    repository: ContainerRegistryRepository
    # admin_repository is now consolidated into repository
    # For backward compatibility, admin_repository references the same repository instance
    admin_repository: ContainerRegistryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ContainerRegistryRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=repository,  # Both fields point to the same instance
        )
