from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs

from .repository import StorageNamespaceRepository


@dataclass
class StorageNamespaceRepositories:
    repository: StorageNamespaceRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=StorageNamespaceRepository(
                db=args.db,
            ),
        )
