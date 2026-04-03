from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.config import ModelDefinition
from ai.backend.manager.data.deployment_revision_preset.types import ResourceSlotEntryData
from ai.backend.manager.models.base import ResourceOptsEntry
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.types import PresetValueEntry
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class DeploymentRevisionPresetUpdaterSpec(UpdaterSpec[DeploymentRevisionPresetRow]):
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    image_id: TriState[uuid.UUID] = field(default_factory=TriState[uuid.UUID].nop)
    model_definition: TriState[ModelDefinition] = field(
        default_factory=TriState[ModelDefinition].nop
    )
    resource_slots: OptionalState[list[ResourceSlotEntryData]] = field(
        default_factory=OptionalState[list[ResourceSlotEntryData]].nop
    )
    resource_opts: OptionalState[list[ResourceOptsEntry]] = field(
        default_factory=OptionalState[list[ResourceOptsEntry]].nop
    )
    cluster_mode: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    cluster_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    startup_command: TriState[str] = field(default_factory=TriState[str].nop)
    bootstrap_script: TriState[str] = field(default_factory=TriState[str].nop)
    environ: OptionalState[dict[str, str]] = field(
        default_factory=OptionalState[dict[str, str]].nop
    )
    preset_values: OptionalState[list[PresetValueEntry]] = field(
        default_factory=OptionalState[list[PresetValueEntry]].nop
    )

    @property
    @override
    def row_class(self) -> type[DeploymentRevisionPresetRow]:
        return DeploymentRevisionPresetRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.rank.update_dict(to_update, "rank")
        self.image_id.update_dict(to_update, "image_id")
        self.model_definition.update_dict(to_update, "model_definition")
        self.resource_opts.update_dict(to_update, "resource_opts")
        self.cluster_mode.update_dict(to_update, "cluster_mode")
        self.cluster_size.update_dict(to_update, "cluster_size")
        self.startup_command.update_dict(to_update, "startup_command")
        self.bootstrap_script.update_dict(to_update, "bootstrap_script")
        self.environ.update_dict(to_update, "environ")
        self.preset_values.update_dict(to_update, "preset_values")
        return to_update
