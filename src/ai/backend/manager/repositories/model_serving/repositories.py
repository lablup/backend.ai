from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ModelServingRepositories:
    repository: ModelServingRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ModelServingRepository(
            args.db,
            args.v2_ops_provider,
            RbacPermissionCheckRepository(PermissionOpsProvider(args.db), args.config_provider),
        )

        return cls(
            repository=repository,
        )
