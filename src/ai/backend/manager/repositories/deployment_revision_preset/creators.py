from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import override
from uuid import UUID

from ai.backend.common.config import ModelDefinition
from ai.backend.common.types import BinarySize
from ai.backend.manager.data.deployment_revision_preset.types import ResourceSlotEntryData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import DeploymentRevisionPresetConflict
from ai.backend.manager.models.base import ResourceOptsEntry
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.types import PresetValueEntry
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class DeploymentRevisionPresetCreatorSpec(CreatorSpec[DeploymentRevisionPresetRow]):
    runtime_variant_id: UUID
    name: str
    description: str | None
    rank: int
    image_id: UUID
    model_definition: ModelDefinition | None
    resource_slots: list[ResourceSlotEntryData]
    resource_opts: list[ResourceOptsEntry]
    cluster_mode: str
    cluster_size: int
    startup_command: str | None
    bootstrap_script: str | None
    environ: dict[str, str]
    preset_values: list[PresetValueEntry]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=DeploymentRevisionPresetConflict(
                    f"Duplicate deployment revision preset name: {self.name}"
                ),
            ),
        )

    @override
    def build_row(self) -> DeploymentRevisionPresetRow:
        row = DeploymentRevisionPresetRow()
        row.runtime_variant = self.runtime_variant_id
        row.name = self.name
        row.description = self.description
        row.rank = self.rank
        row.image_id = self.image_id
        row.model_definition = self.model_definition
        row.resource_opts = self.resource_opts
        row.cluster_mode = self.cluster_mode
        row.cluster_size = self.cluster_size
        row.startup_command = self.startup_command
        row.bootstrap_script = self.bootstrap_script
        row.environ = self.environ
        row.preset_values = self.preset_values
        row.resource_slot_rows = [
            PresetResourceSlotRow(
                slot_name=entry.resource_type,
                quantity=self._parse_quantity(entry.quantity),
            )
            for entry in self.resource_slots
        ]
        return row

    @staticmethod
    def _parse_quantity(value: str) -> Decimal:
        try:
            return Decimal(value)
        except InvalidOperation:
            return Decimal(BinarySize.from_str(value))
