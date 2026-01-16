from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class DomainRepositories:
    repository: DomainRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = DomainRepository(args.db)

        return cls(
            repository=repository,
        )
