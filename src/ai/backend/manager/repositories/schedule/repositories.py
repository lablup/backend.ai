from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.schedule.repository import ScheduleRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ScheduleRepositories:
    repository: ScheduleRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ScheduleRepository(args.db, args.valkey_stat_client, args.config_provider)

        return cls(
            repository=repository,
        )
