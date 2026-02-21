from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.project_config.repository import ProjectConfigRepository
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ProjectConfigRepositories:
    repository: ProjectConfigRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        repository = ProjectConfigRepository(args.db)

        return cls(
            repository=repository,
        )
