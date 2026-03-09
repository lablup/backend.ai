from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.events.repository import EventsRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class EventsRepositories:
    repository: EventsRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = EventsRepository(args.db)
        return cls(
            repository=repository,
        )
