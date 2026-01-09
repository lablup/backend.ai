from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AuthRepositories:
    repository: AuthRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = AuthRepository(args.db)

        return cls(
            repository=repository,
        )
