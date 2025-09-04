from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.domain.admin_repository import AdminDomainRepository
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class DomainRepositories:
    repository: DomainRepository
    admin_repository: AdminDomainRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = DomainRepository(args.db)
        admin_repository = AdminDomainRepository(args.db)

        return cls(
            repository=repository,
            admin_repository=admin_repository,
        )
