from __future__ import annotations

from typing import override

from ai.backend.common.config import ModelDefinition
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.data.deployment.types import (
    DefinitionFiles,
    ModelRevisionSpec,
)
from ai.backend.manager.sokovan.deployment.revision_generator.base import BaseRevisionGenerator


class CustomRevisionGenerator(BaseRevisionGenerator):
    """
    Revision processor for CUSTOM runtime variant.

    CUSTOM variant requires additional validation:
    - Model definition (model-definition.toml) must exist and be valid
    """

    @override
    async def validate_revision(self, revision: ModelRevisionSpec) -> None:
        """
        Validate CUSTOM variant revision by checking model definition.
        """
        definition_files: DefinitionFiles = (
            await self._deployment_repository.fetch_definition_files(
                vfolder_id=revision.mounts.model_vfolder_id,
                model_definition_path=revision.mounts.model_definition_path,
            )
        )

        try:
            ModelDefinition.model_validate(definition_files.model_definition)
        except Exception as e:
            raise InvalidAPIParameters(f"Invalid model definition for CUSTOM variant: {e}") from e
