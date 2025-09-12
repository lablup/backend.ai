from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ResourcePresetRepositories:
    repository: ResourcePresetRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=ResourcePresetRepository(
                args.db, args.valkey_stat_client, args.config_provider
            ),
        )
