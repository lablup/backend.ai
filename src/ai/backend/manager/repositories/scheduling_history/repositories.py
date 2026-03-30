from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.scheduling_history.repository import (
    SchedulingHistoryRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class SchedulingHistoryRepositories:
    repository: SchedulingHistoryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = SchedulingHistoryRepository(args.db)

        return cls(
            repository=repository,
        )
