"""CreatorSpec for deployment revision creation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, override

from ai.backend.common.config import ModelDefinition
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import (
    MountInfoEntry,
    ResourceSlot,
)
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.types import PresetValueEntry
from ai.backend.manager.models.resource_slot.row import DeploymentRevisionResourceSlotRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class DeploymentRevisionCreatorSpec(CreatorSpec[DeploymentRevisionRow]):
    """CreatorSpec for deployment revision creation.

    When using create_revision(), revision_number must be set explicitly.
    When using create_revision_with_next_number(), revision_number can be
    left as None — the repository will assign it atomically.
    """

    deployment_id: DeploymentID
    # ``image_id`` is required at the creation path; the persisted row's
    # ``image`` column going SET NULL is strictly a post-hoc state.
    image_id: ImageID
    resource_group: str
    resource_slots: ResourceSlot
    resource_opts: Mapping[str, Any]
    cluster_mode: str
    cluster_size: int
    # ``model_vfolder_id`` is nullable on the ``deployment_revisions.model``
    # column, so a partial revision draft persists a NULL ``model``.
    model_vfolder_id: VFolderUUID | None
    model_mount_destination: str
    model_definition_path: str | None
    model_definition: ModelDefinition | None
    startup_command: str | None
    bootstrap_script: str | None
    environ: Mapping[str, Any]
    callback_url: str | None
    runtime_variant_id: RuntimeVariantID
    extra_mounts: Sequence[MountInfoEntry]
    preset_values: Sequence[PresetValueEntry] = field(default_factory=list)
    revision_preset_id: DeploymentPresetID | None = None
    revision_number: int | None = None

    def with_revision_number(self, revision_number: int) -> DeploymentRevisionCreatorSpec:
        """Return a copy with the given revision_number."""
        return replace(self, revision_number=revision_number)

    @override
    def build_row(self) -> DeploymentRevisionRow:
        if self.revision_number is None:
            raise InternalServerError("revision_number must be set before building a row")
        row = DeploymentRevisionRow(
            endpoint=self.deployment_id,
            revision_number=self.revision_number,
            image=self.image_id,
            model=self.model_vfolder_id,
            model_mount_destination=self.model_mount_destination,
            model_definition_path=self.model_definition_path,
            model_definition=self.model_definition,
            resource_group=self.resource_group,
            resource_opts=self.resource_opts,
            cluster_mode=self.cluster_mode,
            cluster_size=self.cluster_size,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            environ=self.environ,
            callback_url=self.callback_url,
            runtime_variant_id=self.runtime_variant_id,
            extra_mounts=list(self.extra_mounts),
            preset_values=list(self.preset_values),
            revision_preset_id=self.revision_preset_id,
        )
        row.resource_slot_rows = [
            DeploymentRevisionResourceSlotRow(
                slot_name=str(slot_name),
                quantity=quantity,
            )
            for slot_name, quantity in self.resource_slots.items()
        ]
        return row
