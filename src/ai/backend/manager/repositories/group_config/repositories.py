from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.group_config.repository import GroupConfigRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class GroupConfigRepositories:
    repository: GroupConfigRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = GroupConfigRepository(args.db)

        return cls(
            repository=repository,
        )
