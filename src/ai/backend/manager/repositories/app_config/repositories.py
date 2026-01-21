from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.app_config.repository import AppConfigRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AppConfigRepositories:
    repository: AppConfigRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = AppConfigRepository(args.db, args.valkey_stat_client)

        return cls(
            repository=repository,
        )
