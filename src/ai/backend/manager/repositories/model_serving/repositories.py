from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ModelServingRepositories:
    repository: ModelServingRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ModelServingRepository(args.db)

        return cls(
            repository=repository,
        )
