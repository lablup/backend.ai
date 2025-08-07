from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class MetricRepositories:
    repository: MetricRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = MetricRepository(args.db)

        return cls(
            repository=repository,
        )
