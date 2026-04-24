from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.app_config_policy.repository import (
    AppConfigPolicyRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AppConfigPolicyRepositories:
    repository: AppConfigPolicyRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=AppConfigPolicyRepository(args.db))
