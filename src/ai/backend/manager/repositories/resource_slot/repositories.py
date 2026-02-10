"""Resource Slot Repositories wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import ResourceSlotRepository

__all__ = ("ResourceSlotRepositories",)


@dataclass
class ResourceSlotRepositories:
    repository: ResourceSlotRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ResourceSlotRepository(args.db)

        return cls(
            repository=repository,
        )
