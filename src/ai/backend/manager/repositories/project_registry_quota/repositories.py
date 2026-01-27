from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.project_registry_quota.repository import (
    ProjectRegistryQuotaRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ProjectRegistryQuotaRepositories:
    repository: ProjectRegistryQuotaRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=ProjectRegistryQuotaRepository(args.db))
