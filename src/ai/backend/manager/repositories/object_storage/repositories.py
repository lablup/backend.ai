from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs

from .repository import ObjectStorageRepository


@dataclass
class ObjectStorageRepositories:
    repository: ObjectStorageRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=ObjectStorageRepository(
                db=args.db,
            ),
        )
