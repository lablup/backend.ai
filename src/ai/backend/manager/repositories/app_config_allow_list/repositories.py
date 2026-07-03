from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.app_config_allow_list.repository import (
    AppConfigAllowListRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AppConfigAllowListRepositories:
    repository: AppConfigAllowListRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=AppConfigAllowListRepository(args.ops_provider),
        )
