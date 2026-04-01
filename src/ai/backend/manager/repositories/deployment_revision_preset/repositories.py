from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentRevisionPresetRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class DeploymentRevisionPresetRepositories:
    repository: DeploymentRevisionPresetRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=DeploymentRevisionPresetRepository(args.db),
        )
