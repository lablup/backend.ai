from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.session.admin_repository import AdminSessionRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class SessionRepositories:
    repository: SessionRepository
    admin_repository: AdminSessionRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = SessionRepository(args.db)
        admin_repository = AdminSessionRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=admin_repository,
        )
