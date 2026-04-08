from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.login_client_type.repository import (
    LoginClientTypeRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AuthRepositories:
    repository: AuthRepository
    login_client_type: LoginClientTypeRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = AuthRepository(args.db)
        login_client_type_repository = LoginClientTypeRepository(args.db)

        return cls(
            repository=repository,
            login_client_type=login_client_type_repository,
        )
