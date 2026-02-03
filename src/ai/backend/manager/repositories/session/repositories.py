from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class SessionRepositories:
    repository: SessionRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = SessionRepository(args.db)

        return cls(
            repository=repository,
        )
