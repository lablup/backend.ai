from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.container_registry.db_source import ContainerRegistryDBSource
from ai.backend.manager.repositories.container_registry_quota.repository import (
    PerProjectRegistryQuotaRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class PerProjectRegistryQuotaRepositories:
    repository: PerProjectRegistryQuotaRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=PerProjectRegistryQuotaRepository(
                ContainerRegistryDBSource(args.v2_ops_provider)
            )
        )
