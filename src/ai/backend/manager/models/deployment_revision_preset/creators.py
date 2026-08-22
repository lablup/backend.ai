from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.config import PresetModelDefinition
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.preset_resource_slot import PresetResourceSlotID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.types import BinarySize
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import DeploymentRevisionPresetConflict
from ai.backend.manager.models.base import ResourceOptsEntry
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.models.runtime_variant_preset.types import (
    RuntimeVariantPresetValueEntry,
)
from ai.backend.manager.models.specs.creator import FieldCreator, GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = (
    "RANK_GAP",
    "DeploymentPresetCreator",
    "PresetResourceSlotCreator",
)

# Ranks are spaced so a preset can later be placed between two existing ones.
RANK_GAP = 100


def _parse_quantity(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation:
        return Decimal(BinarySize.from_str(value))


@dataclass
class DeploymentPresetCreator(
    GlobalEntityCreator[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """Insert a preset, ranked last within its runtime variant.

    The rank is a subquery in the INSERT rather than a locked read before it, so two
    concurrent inserts can land on the same rank. Rank only orders a catalog, and
    presets are created rarely enough that a tie costs a momentary ordering wobble.
    """

    runtime_variant_id: RuntimeVariantID
    name: str
    description: str | None
    image_id: ImageID
    model_definition: PresetModelDefinition | None
    resource_opts: list[ResourceOptsEntry]
    cluster_mode: str
    cluster_size: int
    startup_command: str | None
    bootstrap_script: str | None
    environ: dict[str, str]
    runtime_variant_preset_values: list[RuntimeVariantPresetValueEntry]
    replica_count: int
    deployment_strategy: DeploymentStrategy
    deployment_strategy_spec: dict[str, Any]
    open_to_public: bool | None = None
    revision_history_limit: int | None = None

    @override
    def entity_id(self, row: DeploymentRevisionPresetRow) -> DeploymentPresetID:
        return row.id

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
    def to_data(self, row: DeploymentRevisionPresetRow) -> DeploymentRevisionPresetData:
        return row.to_data()

    @override
    def build_row(self) -> DeploymentRevisionPresetRow:
        return DeploymentRevisionPresetRow(
            runtime_variant=self.runtime_variant_id,
            name=self.name,
            description=self.description,
            rank=self._next_rank(),
            image_id=self.image_id,
            model_definition=self.model_definition,
            resource_opts=self.resource_opts,
            cluster_mode=self.cluster_mode,
            cluster_size=self.cluster_size,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            environ=self.environ,
            preset_values=self.runtime_variant_preset_values,
            open_to_public=self.open_to_public,
            replica_count=self.replica_count,
            revision_history_limit=self.revision_history_limit,
            deployment_strategy=self.deployment_strategy,
            deployment_strategy_spec=self.deployment_strategy_spec,
        )

    def _next_rank(self) -> sa.sql.elements.ColumnElement[int]:
        return (
            sa.select(sa.func.coalesce(sa.func.max(DeploymentRevisionPresetRow.rank), 0) + RANK_GAP)
            .where(DeploymentRevisionPresetRow.runtime_variant == self.runtime_variant_id)
            .scalar_subquery()
        )


@dataclass
class PresetResourceSlotCreator(
    FieldCreator[DeploymentPresetID, PresetResourceSlotRow, ResourceSlotEntryData]
):
    """Insert one slot quantity of the preset that owns it."""

    entry: ResourceSlotEntryData

    @override
    def field_id(self, row: PresetResourceSlotRow) -> PresetResourceSlotID:
        return PresetResourceSlotID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentPresetID) -> PresetResourceSlotRow:
        return PresetResourceSlotRow(
            preset_id=owner_id,
            slot_name=self.entry.resource_type,
            quantity=_parse_quantity(self.entry.quantity),
        )

    @override
    def to_data(self, row: PresetResourceSlotRow) -> ResourceSlotEntryData:
        return ResourceSlotEntryData(
            resource_type=row.slot_name,
            quantity=str(row.quantity),
        )
