from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.config import PresetModelDefinition
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.models.base import ResourceOptsEntry
from ai.backend.manager.models.deployment_revision_preset.creators import RANK_GAP
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.searchable_fields import (
    DeploymentPresetSearchableFields,
)
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.models.runtime_variant_preset.types import (
    RuntimeVariantPresetValueEntry,
)
from ai.backend.manager.models.specs.created_in import CreatedInPublic
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter, FieldUpserter

__all__ = ("DeploymentPresetUpserter", "PresetResourceSlotUpserter")


@dataclass
class DeploymentPresetUpserter(
    CreatedInPublic[DeploymentRevisionPresetRow],
    EntityUpserter[DeploymentRevisionPresetRow, DeploymentRevisionPresetData],
):
    """Write a preset under its stated id. Conflict key: id.

    An insert ranks it last within its runtime variant; an update keeps the rank."""

    id: DeploymentPresetID
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
    open_to_public: bool | None
    replica_count: int
    revision_history_limit: int | None
    deployment_strategy: DeploymentStrategy
    deployment_strategy_spec: dict[str, Any]

    @override
    def entity_id(self, row: DeploymentRevisionPresetRow) -> DeploymentPresetID:
        return row.id

    @override
    def row_class(self) -> type[DeploymentRevisionPresetRow]:
        return DeploymentRevisionPresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "rank": self._next_rank(), **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "runtime_variant": self.runtime_variant_id,
            "name": self.name,
            "description": self.description,
            "image_id": self.image_id,
            "model_definition": self.model_definition,
            "resource_opts": self.resource_opts,
            "cluster_mode": self.cluster_mode,
            "cluster_size": self.cluster_size,
            "startup_command": self.startup_command,
            "bootstrap_script": self.bootstrap_script,
            "environ": self.environ,
            "preset_values": self.runtime_variant_preset_values,
            "open_to_public": self.open_to_public,
            "replica_count": self.replica_count,
            "revision_history_limit": self.revision_history_limit,
            "deployment_strategy": self.deployment_strategy,
            "deployment_strategy_spec": self.deployment_strategy_spec,
        }

    def _next_rank(self) -> sa.sql.elements.ColumnElement[int]:
        return (
            sa.select(sa.func.coalesce(sa.func.max(DeploymentRevisionPresetRow.rank), 0) + RANK_GAP)
            .where(DeploymentRevisionPresetRow.runtime_variant == self.runtime_variant_id)
            .scalar_subquery()
        )

    @override
    def to_data(self, row: DeploymentRevisionPresetRow) -> DeploymentRevisionPresetData:
        return DeploymentPresetSearchableFields.own.to_data(row)


@dataclass
class PresetResourceSlotUpserter(
    FieldUpserter[DeploymentPresetID, PresetResourceSlotRow, ResourceSlotEntryData]
):
    """Write one slot quantity of a preset. Conflict key: the preset and the slot name."""

    slot_name: str
    quantity: Decimal

    @override
    def row_class(self) -> type[PresetResourceSlotRow]:
        return PresetResourceSlotRow

    @override
    def index_elements(self) -> list[str]:
        return ["preset_id", "slot_name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: DeploymentPresetID) -> dict[str, Any]:
        return {"preset_id": owner_id, "slot_name": self.slot_name, "quantity": self.quantity}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"quantity": self.quantity}

    @override
    def to_data(self, row: PresetResourceSlotRow) -> ResourceSlotEntryData:
        return ResourceSlotEntryData(resource_type=row.slot_name, quantity=str(row.quantity))
