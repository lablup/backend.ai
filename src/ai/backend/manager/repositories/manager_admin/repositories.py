from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import ManagerAdminRepository


@dataclass
class ManagerAdminRepositories:
    repository: ManagerAdminRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=ManagerAdminRepository(db=args.db))
