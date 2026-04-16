"""Abstract base class for variant-specific revision validation.

The merge pipeline (deployment-config.yaml + preset + model-definition.yaml
+ request) lives in ``DeploymentController``; this module only provides the
hook for variants that need extra checks on the final ``ModelRevisionSpec``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.manager.data.deployment.types import ModelRevisionSpec


class RevisionGenerator(ABC):
    """Variant-specific validator for fully-merged model revision specs."""

    @abstractmethod
    async def validate_revision(self, revision: ModelRevisionSpec) -> None:
        """Validate the final revision spec.

        Args:
            revision: Final revision spec to validate

        Raises:
            InvalidAPIParameters: When validation fails
        """
        raise NotImplementedError
