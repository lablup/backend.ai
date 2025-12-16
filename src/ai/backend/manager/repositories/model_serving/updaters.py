from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from typing_extensions import override

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
)
from ai.backend.manager.data.model_serving.modifier import ExtraMount, ImageRef
from ai.backend.manager.models.endpoint import EndpointAutoScalingRuleRow, EndpointRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class EndpointUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for endpoint updates."""

    resource_slots: OptionalState[ResourceSlot] = field(
        default_factory=OptionalState[ResourceSlot].nop
    )
    resource_opts: TriState[dict[str, Any]] = field(default_factory=TriState[dict[str, Any]].nop)
    cluster_mode: OptionalState[ClusterMode] = field(default_factory=OptionalState[ClusterMode].nop)
    cluster_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    replicas: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    desired_session_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    image: TriState[ImageRef] = field(default_factory=TriState.nop)
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    resource_group: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    model_definition_path: TriState[str] = field(default_factory=TriState[str].nop)
    open_to_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    extra_mounts: OptionalState[list[ExtraMount]] = field(
        default_factory=OptionalState[list[ExtraMount]].nop
    )
    environ: TriState[dict[str, str]] = field(default_factory=TriState[dict[str, str]].nop)
    runtime_variant: OptionalState[RuntimeVariant] = field(
        default_factory=OptionalState[RuntimeVariant].nop
    )

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.resource_opts.update_dict(to_update, "resource_opts")
        self.cluster_mode.update_dict(to_update, "cluster_mode")
        self.cluster_size.update_dict(to_update, "cluster_size")
        self.model_definition_path.update_dict(to_update, "model_definition_path")
        self.runtime_variant.update_dict(to_update, "runtime_variant")
        self.resource_group.update_dict(to_update, "resource_group")
        self.desired_session_count.update_dict(to_update, "desired_session_count")
        self.replicas.update_dict(to_update, "replicas")
        self.environ.update_dict(to_update, "environ")
        return to_update

    def replica_count_modified(self) -> bool:
        """Check if replicas field was modified."""
        return self.replicas.optional_value() is not None


@dataclass
class EndpointAutoScalingRuleUpdaterSpec(UpdaterSpec[EndpointAutoScalingRuleRow]):
    """UpdaterSpec for endpoint auto scaling rule updates."""

    metric_source: OptionalState[AutoScalingMetricSource] = field(default_factory=OptionalState.nop)
    metric_name: OptionalState[str] = field(default_factory=OptionalState.nop)
    threshold: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    comparator: OptionalState[AutoScalingMetricComparator] = field(
        default_factory=OptionalState.nop
    )
    step_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    cooldown_seconds: OptionalState[int] = field(default_factory=OptionalState.nop)
    min_replicas: TriState[int] = field(default_factory=TriState.nop)
    max_replicas: TriState[int] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[EndpointAutoScalingRuleRow]:
        return EndpointAutoScalingRuleRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.metric_source.update_dict(to_update, "metric_source")
        self.metric_name.update_dict(to_update, "metric_name")
        self.threshold.update_dict(to_update, "threshold")
        self.comparator.update_dict(to_update, "comparator")
        self.step_size.update_dict(to_update, "step_size")
        self.cooldown_seconds.update_dict(to_update, "cooldown_seconds")
        self.min_replicas.update_dict(to_update, "min_replicas")
        self.max_replicas.update_dict(to_update, "max_replicas")
        return to_update
