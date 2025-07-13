from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.model_serving.admin_repository import (
    AdminModelServingRepository,
)
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository


@dataclass
class ModelServingRepositories:
    repository: ModelServingRepository
    admin_repository: AdminModelServingRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ModelServingRepository(args.db)
        admin_repository = AdminModelServingRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=admin_repository,
        )
