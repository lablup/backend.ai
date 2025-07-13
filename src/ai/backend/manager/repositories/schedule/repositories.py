from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.schedule.repository import ScheduleRepository


@dataclass
class ScheduleRepositories:
    repository: ScheduleRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ScheduleRepository(args.db)

        return cls(
            repository=repository,
        )
