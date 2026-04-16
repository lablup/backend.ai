"""Revision draft generator backed by a DeploymentRevisionPreset."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.config import ModelDefinition
from ai.backend.common.types import ClusterMode
from ai.backend.manager.data.deployment.types import RevisionDraft
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentRevisionPresetRepository,
)


class PresetDraftGenerator:
    """Resolve a revision preset from storage and emit a RevisionDraft.

    The preset is looked up by id; the generator has no knowledge of user
    requests or vfolder-backed sources.
    """

    _preset_repository: DeploymentRevisionPresetRepository

    def __init__(self, preset_repository: DeploymentRevisionPresetRepository) -> None:
        self._preset_repository = preset_repository

    async def generate(self, preset_id: UUID) -> RevisionDraft:
        preset_data = await self._preset_repository.get_by_id(preset_id)
        slot_entries = await self._preset_repository.get_resource_slots(preset_id)

        resource_slots = {slot_name: str(quantity) for slot_name, quantity in slot_entries}
        resource_opts = {o.name: o.value for o in preset_data.resource_opts}
        environ = {e.key: e.value for e in preset_data.environ}
        model_definition: ModelDefinition | None = (
            ModelDefinition(**preset_data.model_definition)
            if preset_data.model_definition
            else None
        )
        return RevisionDraft(
            image_id=preset_data.image_id,
            resource_slots=resource_slots or None,
            resource_opts=resource_opts or None,
            cluster_mode=ClusterMode(preset_data.cluster_mode)
            if preset_data.cluster_mode
            else None,
            cluster_size=preset_data.cluster_size,
            startup_command=preset_data.startup_command,
            bootstrap_script=preset_data.bootstrap_script,
            environ=environ or None,
            model_definition=model_definition,
            preset_values=list(preset_data.preset_values) or None,
        )
