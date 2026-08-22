from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentPresetRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class DeploymentPresetRepositories:
    repository: DeploymentPresetRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(
            repository=DeploymentPresetRepository(args.v2_ops_provider),
        )
