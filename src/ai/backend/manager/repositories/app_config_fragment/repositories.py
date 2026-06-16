from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.app_config_fragment.admin_repository import (
    AppConfigFragmentAdminRepository,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AppConfigFragmentRepositories:
    repository: AppConfigFragmentRepository
    admin_repository: AppConfigFragmentAdminRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=AppConfigFragmentRepository(args.db, args.ops_provider),
            admin_repository=AppConfigFragmentAdminRepository(args.db, args.ops_provider),
        )
