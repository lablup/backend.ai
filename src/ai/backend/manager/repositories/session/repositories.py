from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.container_registry.db_source import ContainerRegistryDBSource
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class SessionRepositories:
    repository: SessionRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = SessionRepository(
            args.db,
            args.v2_ops_provider,
            registry_db_source=ContainerRegistryDBSource(args.v2_ops_provider),
        )

        return cls(
            repository=repository,
        )
