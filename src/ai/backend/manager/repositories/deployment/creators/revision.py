"""CreatorSpec for deployment revision creation."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, override

from ai.backend.common.config import ModelDefinition
from ai.backend.common.types import (
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
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

    endpoint_id: uuid.UUID
    image_id: uuid.UUID | None
    resource_group: str
    resource_slots: ResourceSlot
    resource_opts: Mapping[str, Any]
    cluster_mode: str
    cluster_size: int
    model_id: uuid.UUID | None
    model_mount_destination: str
    model_definition_path: str | None
    model_definition: ModelDefinition | None
    startup_command: str | None
    bootstrap_script: str | None
    environ: Mapping[str, Any]
    callback_url: str | None
    runtime_variant: RuntimeVariant
    extra_mounts: Sequence[VFolderMount]
    preset_values: Sequence[PresetValueEntry] = field(default_factory=list)
    revision_number: int | None = None

    def with_revision_number(self, revision_number: int) -> DeploymentRevisionCreatorSpec:
        """Return a copy with the given revision_number."""
        return replace(self, revision_number=revision_number)

    @override
    def build_row(self) -> DeploymentRevisionRow:
        if self.revision_number is None:
            raise InternalServerError("revision_number must be set before building a row")
        row = DeploymentRevisionRow(
            endpoint=self.endpoint_id,
            revision_number=self.revision_number,
            image=self.image_id,
            model=self.model_id,
            model_mount_destination=self.model_mount_destination,
            model_definition_path=self.model_definition_path,
            model_definition=self.model_definition.model_dump(exclude_none=True, by_alias=True)
            if self.model_definition
            else None,
            resource_group=self.resource_group,
            resource_opts=self.resource_opts,
            cluster_mode=self.cluster_mode,
            cluster_size=self.cluster_size,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            environ=self.environ,
            callback_url=self.callback_url,
            runtime_variant=self.runtime_variant,
            extra_mounts=list(self.extra_mounts),
            preset_values=list(self.preset_values),
        )
        row.resource_slot_rows = [
            DeploymentRevisionResourceSlotRow(
                slot_name=str(slot_name),
                quantity=quantity,
            )
            for slot_name, quantity in self.resource_slots.items()
        ]
        return row
