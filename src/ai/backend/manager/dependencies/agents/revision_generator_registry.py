from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
    RevisionGeneratorRegistryArgs,
)


@dataclass
class RevisionGeneratorRegistryInput:
    """Input required for revision generator registry setup."""

    deployment_repository: DeploymentRepository


class RevisionGeneratorRegistryDependency(
    NonMonitorableDependencyProvider[RevisionGeneratorRegistryInput, RevisionGeneratorRegistry],
):
    """Provides RevisionGeneratorRegistry lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "revision-generator-registry"

    @asynccontextmanager
    async def provide(
        self, setup_input: RevisionGeneratorRegistryInput
    ) -> AsyncIterator[RevisionGeneratorRegistry]:
        """Initialize and provide a revision generator registry.

        Args:
            setup_input: Input containing deployment repository

        Yields:
            Initialized RevisionGeneratorRegistry
        """
        registry = RevisionGeneratorRegistry(
            RevisionGeneratorRegistryArgs(
                deployment_repository=setup_input.deployment_repository,
            )
        )
        yield registry
