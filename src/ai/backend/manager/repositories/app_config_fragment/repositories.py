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
        # Fragment writes bind the fragment to its RBAC scope (see the db_source), so the
        # repository runs on the RBAC-scoped ops provider rather than the plain one.
        return cls(
            repository=AppConfigFragmentRepository(RBACOpsProvider(args.db)),
        )
