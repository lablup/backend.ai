from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource
from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class AutoScalingConditionModifier(PartialModifier):
    metric_source: OptionalState[AutoScalingMetricSource] = field(
        default_factory=OptionalState[AutoScalingMetricSource].nop
    )
    metric_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    threshold: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    comparator: OptionalState[AutoScalingMetricComparator] = field(
        default_factory=OptionalState[AutoScalingMetricComparator].nop
    )

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.metric_source.update_dict(to_update, "metric_source")
        self.metric_name.update_dict(to_update, "metric_name")
        self.threshold.update_dict(to_update, "threshold")
        self.comparator.update_dict(to_update, "comparator")
        return to_update


@dataclass
class AutoScalingActionModifier(PartialModifier):
    step_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    cooldown_seconds: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    min_replicas: OptionalState[Optional[int]] = field(
        default_factory=OptionalState[Optional[int]].nop
    )
    max_replicas: OptionalState[Optional[int]] = field(
        default_factory=OptionalState[Optional[int]].nop
    )

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.step_size.update_dict(to_update, "step_size")
        self.cooldown_seconds.update_dict(to_update, "cooldown_seconds")
        self.min_replicas.update_dict(to_update, "min_replicas")
        self.max_replicas.update_dict(to_update, "max_replicas")
        return to_update


@dataclass
class AutoScalingRuleModifier(PartialModifier):
    condition: AutoScalingConditionModifier
    action: AutoScalingActionModifier
    enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        to_update.update(self.condition.fields_to_update())
        to_update.update(self.action.fields_to_update())
        self.enabled.update_dict(to_update, "enabled")
        return to_update
