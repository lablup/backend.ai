from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)


@dataclass
class ReservoirRegistryRepositories:
    repository: ReservoirRegistryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ReservoirRegistryRepository(args.db)

        return cls(
            repository=repository,
        )
