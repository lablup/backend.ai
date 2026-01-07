from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class GroupRepositories:
    repository: GroupRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = GroupRepository(
            args.db,
            args.config_provider,
            args.valkey_stat_client,
            args.storage_manager,
        )
        return cls(repository=repository)
