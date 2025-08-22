from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.image.repositories import RepositoryArgs


@dataclass
class ArtifactRepositories:
    repository: ArtifactRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ArtifactRepository(args.db)

        return cls(
            repository=repository,
        )
