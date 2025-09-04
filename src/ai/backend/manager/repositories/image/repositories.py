from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.admin_repository import AdminImageRepository
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ImageRepositories:
    repository: ImageRepository
    admin_repository: AdminImageRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ImageRepository(args.db)
        admin_repository = AdminImageRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=admin_repository,
        )
