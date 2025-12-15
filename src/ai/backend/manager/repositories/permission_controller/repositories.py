from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class PermissionControllerRepositories:
    repository: PermissionControllerRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = PermissionControllerRepository(args.db)

        return cls(
            repository=repository,
        )
