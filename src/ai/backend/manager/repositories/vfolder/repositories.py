from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository


@dataclass
class VfolderRepositories:
    repository: VfolderRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = VfolderRepository(args.db)

        return cls(
            repository=repository,
        )
