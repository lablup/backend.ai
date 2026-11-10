"""Deployment repositories configuration."""

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import DeploymentRepository


@dataclass
class DeploymentRepositories:
    """Container for deployment-related repositories."""

    repository: DeploymentRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        """Create deployment repositories."""
        repository = DeploymentRepository(
            args.db,
            args.reconcile_ops_provider,
            args.storage_manager,
            args.valkey_stat_client,
            args.valkey_live_client,
            args.valkey_schedule_client,
            RbacPermissionCheckRepository(PermissionOpsProvider(args.db), args.config_provider),
        )
        return cls(repository=repository)
