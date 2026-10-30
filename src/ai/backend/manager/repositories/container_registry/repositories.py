from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ContainerRegistryRepositories:
    repository: ContainerRegistryRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=ContainerRegistryRepository(args.db, ShareOpsProvider(args.db)))
