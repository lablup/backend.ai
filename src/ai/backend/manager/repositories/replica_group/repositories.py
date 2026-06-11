"""Replica group repositories configuration."""

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import ReplicaGroupRepository


@dataclass
class ReplicaGroupRepositories:
    """Container for replica-group-related repositories."""

    repository: ReplicaGroupRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        """Create replica group repositories."""
        return cls(repository=ReplicaGroupRepository(args.db))
