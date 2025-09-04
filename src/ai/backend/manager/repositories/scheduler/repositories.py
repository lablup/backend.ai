from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class SchedulerRepositories:
    repository: SchedulerRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = SchedulerRepository(args.db, args.valkey_stat_client, args.config_provider)

        return cls(
            repository=repository,
        )
