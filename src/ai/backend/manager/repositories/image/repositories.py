from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ImageRepositories:
    repository: ImageRepository
    # admin_repository is now consolidated into repository
    # For backward compatibility, admin_repository references the same repository instance
    admin_repository: ImageRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ImageRepository(args.db, args.valkey_image_client, args.config_provider)

        return cls(
            repository=repository,
            admin_repository=repository,  # Both fields point to the same instance
        )
