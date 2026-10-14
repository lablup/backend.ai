from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.system_session_environ.repository import (
    SystemSessionEnvironRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs

__all__ = ("SystemSessionEnvironRepositories",)


@dataclass
class SystemSessionEnvironRepositories:
    repository: SystemSessionEnvironRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=SystemSessionEnvironRepository(args.v2_ops_provider))
