"""Resource-group schemas shared between the manager and its data layer.

Pydantic schema definitions usable as pydantic column types (persisted as
JSON inside the ``scaling_groups.scheduler_opts`` column of the legacy-named
resource group table).
"""

from __future__ import annotations

from datetime import timedelta

from pydantic import ConfigDict, field_serializer

from ai.backend.common.types import BackendAISchema, PreemptionMode, PreemptionOrder

__all__ = ("PreemptionConfig",)


class PreemptionConfig(BackendAISchema):
    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    """Whether preemption is enabled for this resource group (opt-in)"""

    preemptible_priority: int = 5
    """Sessions with priority <= this value are preemptible"""

    order: PreemptionOrder = PreemptionOrder.OLDEST
    """Tie-breaking order for same-priority sessions"""

    mode: PreemptionMode = PreemptionMode.TERMINATE
    """How to preempt sessions"""

    preemption_min_runtime: timedelta = timedelta(seconds=0)
    """Minimum session runtime before it becomes preemptible (0 = disabled)"""

    @field_serializer("order", mode="plain")
    def serialize_order(self, value: PreemptionOrder) -> str:
        return value.value

    @field_serializer("mode", mode="plain")
    def serialize_mode(self, value: PreemptionMode) -> str:
        return value.value

    @field_serializer("preemption_min_runtime", mode="plain")
    def serialize_preemption_min_runtime(self, value: timedelta) -> float:
        return value.total_seconds()
