"""Abstract base class for model revision generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from ai.backend.manager.data.deployment.types import (
    DeploymentConfig,
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
)


class RevisionGenerator(ABC):
    """
    Abstract base class for generating model revisions.

    Different runtime variants may have different validation rules,
    but all share the same override logic.
    """

    @abstractmethod
    async def generate_revision(
        self,
        draft_revision: ModelRevisionSpecDraft,
        vfolder_id: UUID,
        default_architecture: str | None = None,
    ) -> ModelRevisionSpec:
        """
        Process draft revision by loading deployment config and merging.

        Args:
            draft_revision: Draft model revision from API
            vfolder_id: VFolder ID containing model definition and deployment config
            default_architecture: Default architecture from scaling group agents

        Returns:
            Final ModelRevisionSpec ready for deployment

        Raises:
            InvalidAPIParameters: When validation fails
        """
        raise NotImplementedError

    @abstractmethod
    async def load_deployment_config(
        self,
        vfolder_id: UUID,
        runtime_variant: str,
    ) -> DeploymentConfig | None:
        """
        Load deployment config from vfolder.

        Args:
            vfolder_id: VFolder ID containing deployment config
            runtime_variant: Runtime variant to load config for

        Returns:
            DeploymentConfig if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def merge_revision(
        self,
        draft_revision: ModelRevisionSpecDraft,
        deployment_config: DeploymentConfig | None,
        default_architecture: str | None = None,
    ) -> ModelRevisionSpec:
        """
        Merge draft revision with deployment config.

        Args:
            draft_revision: Draft model revision from API
            deployment_config: Optional deployment config from file
            default_architecture: Default architecture from scaling group agents

        Returns:
            Merged ModelRevisionSpec

        Raises:
            InvalidAPIParameters: When required fields are missing
        """
        raise NotImplementedError

    @abstractmethod
    async def validate_revision(self, revision: ModelRevisionSpec) -> None:
        """
        Validate the final revision spec.

        This is called after merging and allows variant-specific validation.
        For example, CUSTOM variant may validate model definition existence.

        Args:
            revision: Final revision spec to validate

        Raises:
            InvalidAPIParameters: When validation fails
        """
        raise NotImplementedError
