"""Resource Usage History Repositories wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import ResourceUsageHistoryRepository

__all__ = ("ResourceUsageHistoryRepositories",)


@dataclass
class ResourceUsageHistoryRepositories:
    repository: ResourceUsageHistoryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ResourceUsageHistoryRepository(args.db)

        return cls(
            repository=repository,
        )
