from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class SchedulerRepositories:
    repository: SchedulerRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = SchedulerRepository(
            args.db,
            args.reconcile_ops_provider,
            args.valkey_stat_client,
            args.valkey_schedule_client,
            args.config_provider,
            args.storage_manager,
            RbacPermissionCheckRepository(PermissionOpsProvider(args.db), args.config_provider),
        )

        return cls(
            repository=repository,
        )
