"""Registry for managing revision processors by runtime variant."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.revision_generator.abc import (
    RevisionGenerator,
)
from ai.backend.manager.sokovan.deployment.revision_generator.base import (
    BaseRevisionGenerator,
)


@dataclass
class RevisionGeneratorRegistryArgs:
    deployment_repository: DeploymentRepository


class RevisionGeneratorRegistry:
    """
    Registry for managing revision processors by runtime variant.

    All variants use the same BaseRevisionGenerator which handles:
    - Service definition loading and merging
    - Model definition validation (if file exists)
    - CUSTOM variant requires model-definition.yml to exist
    """

    _generator: RevisionGenerator

    def __init__(self, args: RevisionGeneratorRegistryArgs) -> None:
        # All variants use the same base generator
        # BaseRevisionGenerator handles model-definition.yml validation for all variants
        self._generator = BaseRevisionGenerator(args.deployment_repository)

    def get(self) -> RevisionGenerator:
        # TODO: If no variant-specific generators are needed in the future,
        # consider removing this registry class and using BaseRevisionGenerator directly.
        return self._generator
