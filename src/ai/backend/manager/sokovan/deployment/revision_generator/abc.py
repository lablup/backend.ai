"""Abstract base class for model revision generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from ai.backend.manager.data.deployment.types import (
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
    ModelServiceDefinition,
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
        model_definition_path: Optional[str],
        default_architecture: Optional[str] = None,
    ) -> ModelRevisionSpec:
        """
        Process draft revision by loading service definition and merging.

        Args:
            draft_revision: Draft model revision from API
            vfolder_id: VFolder ID containing model and service definition
            model_definition_path: Optional path to model definition directory
            default_architecture: Default architecture from scaling group agents

        Returns:
            Final ModelRevisionSpec ready for deployment

        Raises:
            InvalidAPIParameters: When validation fails
        """
        raise NotImplementedError()

    @abstractmethod
    async def load_service_definition(
        self,
        vfolder_id: UUID,
        model_definition_path: Optional[str],
        runtime_variant: str,
    ) -> Optional[ModelServiceDefinition]:
        """
        Load service definition from vfolder.

        Args:
            vfolder_id: VFolder ID containing service definition
            model_definition_path: Optional path to service definition file
            runtime_variant: Runtime variant to load definition for

        Returns:
            Service definition if found, None otherwise
        """
        raise NotImplementedError()

    @abstractmethod
    def merge_revision(
        self,
        draft_revision: ModelRevisionSpecDraft,
        service_definition: Optional[ModelServiceDefinition],
        default_architecture: Optional[str] = None,
    ) -> ModelRevisionSpec:
        """
        Merge draft revision with service definition.

        Args:
            draft_revision: Draft model revision from API
            service_definition: Optional service definition from file
            default_architecture: Default architecture from scaling group agents

        Returns:
            Merged ModelRevisionSpec

        Raises:
            InvalidAPIParameters: When required fields are missing
        """
        raise NotImplementedError()

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
        raise NotImplementedError()
