"""Base implementation of revision validator (no-op default)."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.deployment.types import ModelRevisionSpec
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.revision_generator.abc import RevisionGenerator


class BaseRevisionGenerator(RevisionGenerator):
    """Default validator used by variants with no extra constraints.

    Subclasses override ``validate_revision`` for variant-specific rules
    (e.g., CUSTOM checks that model-definition.toml exists and is valid).
    """

    _deployment_repository: DeploymentRepository

    def __init__(self, deployment_repository: DeploymentRepository) -> None:
        self._deployment_repository = deployment_repository

    @override
    async def validate_revision(self, revision: ModelRevisionSpec) -> None:
        return
