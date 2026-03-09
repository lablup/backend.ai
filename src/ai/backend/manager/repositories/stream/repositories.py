from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.stream.repository import StreamRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class StreamRepositories:
    repository: StreamRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = StreamRepository(args.db)
        return cls(
            repository=repository,
        )
