from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from .repository import AppConfigRepository

if TYPE_CHECKING:
    from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AppConfigRepositories:
    repository: AppConfigRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=AppConfigRepository(args.v2_ops_provider))
