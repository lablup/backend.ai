from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class SessionRepositories:
    repository: SessionRepository
    # admin_repository is now consolidated into repository
    # For backward compatibility, admin_repository references the same repository instance
    admin_repository: SessionRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = SessionRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=repository,  # Both fields point to the same instance
        )
