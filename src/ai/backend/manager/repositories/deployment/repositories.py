"""Deployment repositories configuration."""

from dataclasses import dataclass
from typing import Self

from ..types import RepositoryArgs
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
            args.storage_manager,
            args.valkey_stat_client,
            args.valkey_live_client,
            args.valkey_schedule_client,
        )
        return cls(repository=repository)
