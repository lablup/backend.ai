from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.user.repository import UserRepository


@dataclass
class UserRepositories:
    repository: UserRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = UserRepository(args.db)

        return cls(
            repository=repository,
        )
