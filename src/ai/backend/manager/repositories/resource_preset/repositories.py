from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository


@dataclass
class ResourcePresetRepositories:
    repository: ResourcePresetRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ResourcePresetRepository(args.db)

        return cls(
            repository=repository,
        )
