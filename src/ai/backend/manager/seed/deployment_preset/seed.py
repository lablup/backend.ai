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
from ai.backend.common.exception import BackendAIError
from ai.backend.common.schema.deployment import BlueGreenSpec, RollingUpdateSpec
from ai.backend.common.types import ClusterMode
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
    def check(self) -> list[str]:
        """The rules the create API applies to the cluster, the replicas, the strategy spec
        and the model definition."""
        failures: list[str] = []
        try:
            ClusterMode(self.cluster_mode)
        except ValueError:
            modes = sorted(mode.value for mode in ClusterMode)
            failures.append(f"cluster_mode {self.cluster_mode!r} is not one of {modes}")
        if self.cluster_size < 1:
            failures.append(f"cluster_size {self.cluster_size} is below 1")
        if self.replica_count < 0:
            failures.append(f"replica_count {self.replica_count} is negative")
        if self.revision_history_limit is not None and self.revision_history_limit < 0:
            failures.append(f"revision_history_limit {self.revision_history_limit} is negative")
        failures.extend(self._strategy_spec_failures())
        if self.model_definition is not None:
            failures.extend(self._model_definition_failures(self.model_definition))
        return failures

    def _strategy_spec_failures(self) -> list[str]:
        if not self.deployment_strategy_spec:
            return []
        spec = (
            RollingUpdateSpec
            if self.deployment_strategy is DeploymentStrategy.ROLLING
            else BlueGreenSpec
        )
        try:
            parsed = spec.model_validate(self.deployment_strategy_spec)
        except BackendAIError as e:
            return [f"deployment_strategy_spec does not fit {self.deployment_strategy}: {e}"]
        if isinstance(parsed, BlueGreenSpec) and parsed.promote_delay_seconds < 0:
            return ["deployment_strategy_spec.promote_delay_seconds is negative"]
        return []

    def _model_definition_failures(self, definition: PresetModelDefinition) -> list[str]:
        if len(definition.models) != 1:
            return [f"model_definition states {len(definition.models)} models; exactly 1"]
        model = definition.models[0]
        failures = [
            f"model_definition {name} is empty"
            for name, value in (("name", model.name), ("model_path", model.model_path))
            if value == ""
        ]
        if model.service is None:
            failures.append("model_definition service is left out")
            return failures
        health_check = model.service.health_check
        if health_check is None:
            return failures
        if (
            health_check.expected_status_code is not None
            and health_check.expected_status_code <= 100
        ):
            failures.append(
                f"health_check expected_status_code {health_check.expected_status_code} is not above 100"
            )
        if health_check.initial_delay is not None and health_check.initial_delay < 0:
            failures.append(f"health_check initial_delay {health_check.initial_delay} is negative")
        return failures

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[DeploymentPresetSeed]]) -> list[SeedRejection]:
        return []
