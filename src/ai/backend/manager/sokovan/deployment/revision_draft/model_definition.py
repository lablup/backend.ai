"""Revision draft generator backed by model-definition.yaml (via generator registry)."""

from __future__ import annotations

import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import ExecutionSpec, MountMetadata, RevisionDraft
from ai.backend.manager.sokovan.deployment.definition_generator.base import ModelDefinitionContext
from ai.backend.manager.sokovan.deployment.definition_generator.registry import (
    ModelDefinitionGeneratorRegistry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelDefinitionDraftGenerator:
    """Produce a RevisionDraft carrying the vfolder/variant-resolved ModelDefinition.

    Delegates to ``ModelDefinitionGeneratorRegistry`` for the variant-specific
    programmatic generation and vfolder file merge. User-provided overrides are
    NOT consumed here — they travel on the request draft and are merged later
    by ``merge_revision_drafts``.
    """

    _registry: ModelDefinitionGeneratorRegistry

    def __init__(self, registry: ModelDefinitionGeneratorRegistry) -> None:
        self._registry = registry

    async def generate(
        self,
        mounts: MountMetadata,
        execution: ExecutionSpec,
    ) -> RevisionDraft:
        context = ModelDefinitionContext(
            mounts=MountMetadata(
                model_vfolder_id=mounts.model_vfolder_id,
                model_definition_path=mounts.model_definition_path,
                model_mount_destination=mounts.model_mount_destination,
            ),
            execution=execution,
            model_definition=None,
        )
        try:
            definition = await self._registry.generate_model_definition(context)
        except Exception:
            log.warning(
                "Failed to resolve model definition for vfolder {}, proceeding without it",
                mounts.model_vfolder_id,
                exc_info=True,
            )
            return RevisionDraft()
        return RevisionDraft(model_definition=definition)
