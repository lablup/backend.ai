from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ArtifactRegistryRepositories:
    repository: ArtifactRegistryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ArtifactRegistryRepository(args.db)

        return cls(
            repository=repository,
        )
