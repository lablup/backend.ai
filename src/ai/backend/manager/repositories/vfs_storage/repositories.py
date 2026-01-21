from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs

from .repository import VFSStorageRepository


@dataclass
class VFSStorageRepositories:
    repository: VFSStorageRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=VFSStorageRepository(
                db=args.db,
            ),
        )
