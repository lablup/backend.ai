from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.retention.repository import RetentionRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class RetentionRepositories:
    repository: RetentionRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=RetentionRepository(args.ops_provider, args.config_provider),
        )
