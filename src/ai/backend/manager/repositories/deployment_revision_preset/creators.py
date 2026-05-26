from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, override

from ai.backend.common.config import ModelDefinition
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.types import BinarySize
from ai.backend.manager.data.deployment_revision_preset.types import ResourceSlotEntryData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import DeploymentRevisionPresetConflict
from ai.backend.manager.models.base import ResourceOptsEntry
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.types import PresetValueEntry
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.repositories.base.creator import CreatorSpec, DependentCreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


def _parse_quantity(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation:
        return Decimal(BinarySize.from_str(value))


@dataclass
class DeploymentRevisionPresetCreatorSpec(CreatorSpec[DeploymentRevisionPresetRow]):
    runtime_variant_id: RuntimeVariantID
    name: str
    description: str | None
    rank: int
    image_id: ImageID
    model_definition: ModelDefinition | None
    resource_opts: list[ResourceOptsEntry]
    cluster_mode: str
    cluster_size: int
    startup_command: str | None
    bootstrap_script: str | None
    environ: dict[str, str]
    preset_values: list[PresetValueEntry]
    replica_count: int
    deployment_strategy: DeploymentStrategy
    deployment_strategy_spec: dict[str, Any]
    open_to_public: bool | None = None
    revision_history_limit: int | None = None

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
        return DeploymentRevisionPresetRow(
            runtime_variant=self.runtime_variant_id,
            name=self.name,
            description=self.description,
            rank=self.rank,
            image_id=self.image_id,
            model_definition=self.model_definition,
            resource_opts=self.resource_opts,
            cluster_mode=self.cluster_mode,
            cluster_size=self.cluster_size,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            environ=self.environ,
            preset_values=self.preset_values,
            open_to_public=self.open_to_public,
            replica_count=self.replica_count,
            revision_history_limit=self.revision_history_limit,
            deployment_strategy=self.deployment_strategy,
            deployment_strategy_spec=self.deployment_strategy_spec,
        )


@dataclass(frozen=True)
class PresetSlotDependency:
    """Dependency value for creating preset resource slots: the owning preset's id."""

    preset_id: uuid.UUID


@dataclass
class PresetResourceSlotDependentCreatorSpec(
    DependentCreatorSpec[PresetSlotDependency, PresetResourceSlotRow]
):
    entry: ResourceSlotEntryData

    @override
    def build_row(self, dependency: PresetSlotDependency) -> PresetResourceSlotRow:
        return PresetResourceSlotRow(
            preset_id=dependency.preset_id,
            slot_name=self.entry.resource_type,
            quantity=_parse_quantity(self.entry.quantity),
        )
