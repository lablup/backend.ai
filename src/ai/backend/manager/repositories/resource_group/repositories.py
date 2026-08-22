from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ResourceGroupRepositories:
    repository: ResourceGroupRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ResourceGroupRepository(
            args.db,
        )

        return cls(
            repository=repository,
        )
