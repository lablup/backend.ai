from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Annotated, Any, override

from pydantic import Field, StringConstraints

from ai.backend.common.config import PresetModelDefinition
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.models.base import ResourceOptsEntry
from ai.backend.manager.models.deployment_revision_preset.purgers import (
    PresetResourceSlotUnstatedPurger,
)
from ai.backend.manager.models.deployment_revision_preset.upserters import (
    DeploymentPresetUpserter,
    PresetResourceSlotUpserter,
)
from ai.backend.manager.models.runtime_variant_preset.types import (
    RuntimeVariantPresetValueEntry,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class DeploymentPresetSeed(SeedItem):
    """One ``deployment_revision_presets`` row under its stated id, with the slot
    quantities it declares (``resource_slots``)."""

    id: DeploymentPresetID
    runtime_variant_id: RuntimeVariantID
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    image_id: ImageID
    model_definition: PresetModelDefinition | None = None
    resource_slots: dict[
        Annotated[str, StringConstraints(min_length=1, max_length=64)],
        Annotated[Decimal, Field(max_digits=24, decimal_places=6)],
    ] = {}
    resource_opts: list[ResourceOptsEntry] = []
    cluster_mode: str = Field(default="single-node", min_length=1, max_length=16)
    cluster_size: int = Field(default=1, ge=-(2**31), le=2**31 - 1)
    startup_command: str | None = None
    bootstrap_script: str | None = None
    environ: dict[str, str] = {}
    runtime_variant_preset_values: list[RuntimeVariantPresetValueEntry] = []
    open_to_public: bool | None = None
    replica_count: int = Field(default=1, ge=-(2**31), le=2**31 - 1)
    revision_history_limit: int | None = Field(default=None, ge=-(2**31), le=2**31 - 1)
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    deployment_strategy_spec: dict[str, Any] = {}

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        """The preset, one row per stated slot, and under an overwrite the slot rows the
        file leaves out."""
        return SeedWrite(
            upserter=DeploymentPresetUpserter(
                id=self.id,
                runtime_variant_id=self.runtime_variant_id,
                name=self.name,
                description=self.description,
                image_id=self.image_id,
                model_definition=self.model_definition,
                resource_opts=self.resource_opts,
                cluster_mode=self.cluster_mode,
                cluster_size=self.cluster_size,
                startup_command=self.startup_command,
                bootstrap_script=self.bootstrap_script,
                environ=self.environ,
                runtime_variant_preset_values=self.runtime_variant_preset_values,
                open_to_public=self.open_to_public,
                replica_count=self.replica_count,
                revision_history_limit=self.revision_history_limit,
                deployment_strategy=self.deployment_strategy,
                deployment_strategy_spec=self.deployment_strategy_spec,
            ),
            field_upserters=[
                PresetResourceSlotUpserter(slot_name=slot_name, quantity=quantity)
                for slot_name, quantity in sorted(self.resource_slots.items())
            ],
            field_purgers=[PresetResourceSlotUnstatedPurger(slot_names=list(self.resource_slots))],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[DeploymentPresetSeed]]) -> list[SeedRejection]:
        return []
