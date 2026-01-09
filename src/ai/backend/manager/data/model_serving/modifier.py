import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, override

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
)
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class ImageRef:
    name: str
    registry: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    architecture: OptionalState[str] = field(default_factory=OptionalState[str].nop)


@dataclass
class ExtraMount:
    vfolder_id: OptionalState[uuid.UUID] = field(default_factory=OptionalState[uuid.UUID].nop)
    mount_destination: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    type: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    permission: OptionalState[str] = field(default_factory=OptionalState[str].nop)


@dataclass
class EndpointModifier(PartialModifier):
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

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.resource_opts.update_dict(to_update, "resource_opts")
        self.cluster_mode.update_dict(to_update, "cluster_mode")
        self.cluster_size.update_dict(to_update, "cluster_size")
        self.model_definition_path.update_dict(to_update, "model_definition_path")
        self.runtime_variant.update_dict(to_update, "runtime_variant")
        self.resource_group.update_dict(to_update, "resource_group")
        return to_update

    def fields_to_update_require_none_check(self) -> dict[str, Any]:
        # This method is used to update fields that require a check for None values
        to_update: dict[str, Any] = {}
        # The order of replicas and desired_session_count is important
        # as desired_session_count is legacy field and value of replicas need to override it
        self.desired_session_count.update_dict(to_update, "desired_session_count")
        self.replicas.update_dict(to_update, "replicas")
        self.environ.update_dict(to_update, "environ")
        return to_update

    def replica_count_modified(self) -> bool:
        return self.replicas.optional_value() is not None


@dataclass
class EndpointAutoScalingRuleModifier(PartialModifier):
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

    @override
    def fields_to_update(self) -> dict[str, Any]:
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
