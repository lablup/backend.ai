from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import ArtifactStorageRepository


@dataclass
class ArtifactStorageRepositories:
    repository: ArtifactStorageRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=ArtifactStorageRepository(
                db=args.db,
            ),
        )
