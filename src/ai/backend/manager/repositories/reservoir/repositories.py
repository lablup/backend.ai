from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.reservoir.repository import ReservoirRepository


@dataclass
class ReservoirRepositories:
    repository: ReservoirRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ReservoirRepository(args.db)

        return cls(
            repository=repository,
        )
