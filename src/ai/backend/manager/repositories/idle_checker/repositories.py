"""Idle Checker Repositories wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs

from .repository import IdleCheckerRepository

__all__ = ("IdleCheckerRepositories",)


@dataclass
class IdleCheckerRepositories:
    repository: IdleCheckerRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = IdleCheckerRepository(args.db)

        return cls(
            repository=repository,
        )
