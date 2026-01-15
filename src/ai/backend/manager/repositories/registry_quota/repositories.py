from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.registry_quota.repository import (
    RegistryQuotaRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class RegistryQuotaRepositories:
    repository: RegistryQuotaRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=RegistryQuotaRepository(args.db))
