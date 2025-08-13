from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.user.admin_repository import AdminUserRepository
from ai.backend.manager.repositories.user.repository import UserRepository


@dataclass
class UserRepositories:
    repository: UserRepository
    admin_repository: AdminUserRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = UserRepository(args.db)
        admin_repository = AdminUserRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=admin_repository,
        )
