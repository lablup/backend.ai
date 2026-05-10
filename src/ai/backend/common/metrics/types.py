from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Self

from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.types import KernelId

UNDEFINED: Final[str] = "undefined"

UTILIZATION_METRIC_INTERVAL: Final[float] = 5.0
UTILIZATION_METRIC_DETENTION: Final[float] = 600.0  # 10 minutes

CONTAINER_UTILIZATION_METRIC_NAME: Final[str] = "backendai_container_utilization"
CONTAINER_UTILIZATION_METRIC_LABEL_NAME: Final[str] = "container_metric_name"
DEVICE_UTILIZATION_METRIC_LABEL_NAME: Final[str] = "device_metric_name"
PROCESS_UTILIZATION_METRIC_LABEL_NAME: Final[str] = "process_metric_name"

# Stand-in capacity for metrics whose Prometheus capacity series does not exist.
CAPACITY_SENTINEL: Final[str] = "9223372036854775807"  # 2**63 - 1

CAPACITY_SENTINEL_METRICS: Final[frozenset[str]] = frozenset({
    "cpu_used",
    "net_rx",
    "net_tx",
    "io_read",
    "io_write",
})


@dataclass(frozen=True)
class KernelLiveStatValues:
    values_by_kernel: Mapping[KernelId, list[MetricValue]]

    @classmethod
    def with_capacity_sentinels(
        cls,
        values_by_kernel: Mapping[KernelId, list[MetricValue]],
    ) -> Self:
        """For metrics in `CAPACITY_SENTINEL_METRICS` that are live (have a
        CURRENT sample) but lack a Prometheus capacity series, append a
        synthetic CAPACITY sample carrying `CAPACITY_SENTINEL`. Existing
        capacity values are preserved.
        """
        new_values: dict[KernelId, list[MetricValue]] = {
            kid: list(vs) for kid, vs in values_by_kernel.items()
        }
        for vs in new_values.values():
            reported_currents: set[str] = set()
            reported_capacities: set[str] = set()
            for v in vs:
                if v.value_type is ValueType.CURRENT:
                    reported_currents.add(v.metric_name)
                elif v.value_type is ValueType.CAPACITY:
                    reported_capacities.add(v.metric_name)
            sentinel_targets = (reported_currents & CAPACITY_SENTINEL_METRICS) - reported_capacities
            for metric_name in sentinel_targets:
                vs.append(
                    MetricValue(
                        metric_name=metric_name,
                        value_type=ValueType.CAPACITY,
                        value=CAPACITY_SENTINEL,
                    )
                )
        return cls(values_by_kernel=new_values)
