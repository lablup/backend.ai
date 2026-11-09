from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from .repository import StorageStatusRepository

if TYPE_CHECKING:
    from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class StorageStatusRepositories:
    repository: StorageStatusRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=StorageStatusRepository(args.storage_status_ops_provider))
