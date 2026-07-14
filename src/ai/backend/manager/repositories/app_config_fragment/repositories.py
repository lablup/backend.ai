from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AppConfigFragmentRepositories:
    repository: AppConfigFragmentRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        # Fragment writes bind to an RBAC scope (see db_source), so use the RBAC ops provider.
        return cls(
            repository=AppConfigFragmentRepository(RBACOpsProvider(args.db)),
        )
