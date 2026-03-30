from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.notification.repository import NotificationRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class NotificationRepositories:
    repository: NotificationRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = NotificationRepository(args.db)

        return cls(
            repository=repository,
        )
