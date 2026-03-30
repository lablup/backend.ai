from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import EtcdConfigRepository


@dataclass
class EtcdConfigRepositories:
    repository: EtcdConfigRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=EtcdConfigRepository(db=args.db))
