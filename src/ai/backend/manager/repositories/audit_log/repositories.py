from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import AuditLogRepository


@dataclass
class AuditLogRepositories:
    repository: AuditLogRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=AuditLogRepository(db=args.db),
        )
