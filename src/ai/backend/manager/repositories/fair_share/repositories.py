"""Fair Share Repositories wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import FairShareRepository

__all__ = ("FairShareRepositories",)


@dataclass
class FairShareRepositories:
    repository: FairShareRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = FairShareRepository(args.db)

        return cls(
            repository=repository,
        )
