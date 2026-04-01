from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.model_card.repository import ModelCardRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ModelCardRepositories:
    repository: ModelCardRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=ModelCardRepository(args.db),
        )
