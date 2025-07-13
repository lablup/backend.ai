from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.image.repositories import RepositoryArgs


@dataclass
class GroupRepositories:
    repository: GroupRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = GroupRepository(args.db)

        return cls(
            repository=repository,
        )
