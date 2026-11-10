from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.entity_share.repository import EntityShareRepository
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class EntityShareRepositories:
    repository: EntityShareRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=EntityShareRepository(ShareOpsProvider(args.db)),
        )
