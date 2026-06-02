from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.role_preset.repository import RolePresetRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class RolePresetRepositories:
    repository: RolePresetRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=RolePresetRepository(args.ops_provider),
        )
