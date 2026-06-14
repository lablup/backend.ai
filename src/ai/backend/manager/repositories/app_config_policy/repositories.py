from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.app_config_policy.admin_repository import (
    AppConfigPolicyAdminRepository,
)
from ai.backend.manager.repositories.app_config_policy.repository import (
    AppConfigPolicyRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AppConfigPolicyRepositories:
    repository: AppConfigPolicyRepository
    admin_repository: AppConfigPolicyAdminRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=AppConfigPolicyRepository(args.ops_provider),
            admin_repository=AppConfigPolicyAdminRepository(args.ops_provider),
        )
