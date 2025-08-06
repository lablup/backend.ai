from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.group.admin_repository import AdminGroupRepository
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class GroupRepositories:
    repository: GroupRepository
    admin_repository: AdminGroupRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = GroupRepository(args.db, args.config_provider, args.valkey_stat_client)
        admin_repository = AdminGroupRepository(args.db, args.storage_manager)

        return cls(
            repository=repository,
            admin_repository=admin_repository,
        )
