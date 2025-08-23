from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.image.repositories import RepositoryArgs


@dataclass
class HuggingFaceRegistryRepositories:
    repository: HuggingFaceRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = HuggingFaceRepository(args.db)

        return cls(
            repository=repository,
        )
