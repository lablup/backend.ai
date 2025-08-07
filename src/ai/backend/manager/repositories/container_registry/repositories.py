from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ContainerRegistryRepositories:
    repository: ContainerRegistryRepository
    admin_repository: AdminContainerRegistryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ContainerRegistryRepository(args.db)
        admin_repository = AdminContainerRegistryRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=admin_repository,
        )
