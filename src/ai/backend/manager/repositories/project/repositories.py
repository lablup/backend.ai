from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ProjectRepositories:
    repository: ProjectRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ProjectRepository(
            args.db,
            args.v2_ops_provider,
            args.config_provider,
            args.valkey_stat_client,
            args.storage_manager,
        )
        return cls(repository=repository)
