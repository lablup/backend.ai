from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.vfolder.admin_repository import VFolderAdminRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository


@dataclass
class VfolderRepositories:
    repository: VfolderRepository
    admin_repository: VFolderAdminRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = VfolderRepository(args.db)
        admin_repository = VFolderAdminRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=admin_repository,
        )
