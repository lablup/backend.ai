from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.metric.repository import MetricRepository


@dataclass
class MetricRepositories:
    repository: MetricRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = MetricRepository(args.db)

        return cls(
            repository=repository,
        )
