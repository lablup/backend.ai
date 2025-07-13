from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.vfolder.admin_repository import AdminVfolderRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository


@dataclass
class VfolderRepositories:
    repository: VfolderRepository
    admin_repository: AdminVfolderRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = VfolderRepository(args.db)
        admin_repository = AdminVfolderRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=admin_repository,
        )
