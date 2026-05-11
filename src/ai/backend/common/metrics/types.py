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
        CURRENT sample), force the CAPACITY sample to `CAPACITY_SENTINEL`.

        These metrics have no meaningful capacity (cumulative counters / rates),
        so any CAPACITY value present in the Prometheus response is a stale
        current-as-fallback artifact and must be overwritten rather than
        respected.
        """
        new_values: dict[KernelId, list[MetricValue]] = {
            kid: list(vs) for kid, vs in values_by_kernel.items()
        }
        for kid, vs in new_values.items():
            reported_currents: set[str] = {
                v.metric_name for v in vs if v.value_type is ValueType.CURRENT
            }
            sentinel_targets = reported_currents & CAPACITY_SENTINEL_METRICS
            if not sentinel_targets:
                continue
            rewritten = [
                v
                for v in vs
                if not (v.value_type is ValueType.CAPACITY and v.metric_name in sentinel_targets)
            ]
            for metric_name in sentinel_targets:
                rewritten.append(
                    MetricValue(
                        metric_name=metric_name,
                        value_type=ValueType.CAPACITY,
                        value=CAPACITY_SENTINEL,
                    )
                )
            new_values[kid] = rewritten
        return cls(values_by_kernel=new_values)
