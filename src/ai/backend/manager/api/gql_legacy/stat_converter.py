from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from typing import Final

from ai.backend.common.clients.prometheus.metric_types import (
    KernelLiveStatBatchResult,
    KernelLiveStatValues,
)
from ai.backend.common.metrics.types import CAPACITY_SENTINEL, CAPACITY_SENTINEL_METRICS
from ai.backend.common.types import KernelId, MetricValue

# Metric-name classification used only while adapting Prometheus samples back
# into the legacy live_stat dict that Graphene/WebUI still expects.
_RATE_STAT_METRICS: Final[frozenset[str]] = frozenset({"net_rx", "net_tx"})
_DIFF_STAT_METRICS: Final[frozenset[str]] = frozenset({"cpu_util"})

# Per-metric unit hint emitted by the agent (source of truth:
# src/ai/backend/agent/docker/intrinsic.py).
_METRIC_UNIT_HINTS: Final[dict[str, str]] = {
    "cpu_used": "msec",
    "cpu_util": "percent",
    "mem": "bytes",
    "net_rx": "bps",
    "net_tx": "bps",
    "io_read": "bytes",
    "io_write": "bytes",
    "io_scratch_size": "bytes",
}


def _make_default_metric_value(unit_hint: str) -> MetricValue:
    return MetricValue({
        "current": "0",
        "capacity": "0",
        "pct": "0",
        "unit_hint": unit_hint,
        "stats.min": "0",
        "stats.max": "0",
        "stats.sum": "0",
        "stats.avg": "0",
        "stats.diff": "0",
        "stats.rate": "0",
        "stats.version": None,
    })


def _resolve_unit_hint(metric_name: str) -> str:
    if metric_name in _METRIC_UNIT_HINTS:
        return _METRIC_UNIT_HINTS[metric_name]
    if metric_name.endswith("_util"):
        return "percent"
    if metric_name == "mem" or metric_name.endswith("_mem"):
        return "bytes"
    if metric_name.startswith("io_"):
        return "bytes"
    if metric_name.startswith("net_"):
        return "bps"
    return metric_name


class LegacyLiveStatConverter:
    """Adapt `KernelLiveStatBatchResult` into the legacy
    `dict[metric_name, MetricValue]` shape consumed by GQL/WebUI.

    The batch result carries per-kernel raw samples partitioned by query type;
    mapping them to legacy ``stats.*`` fields (with rate-over-non-rate
    fallback priority and capacity sentinels for unbounded metrics) is
    performed here.
    """

    @classmethod
    def convert(
        cls,
        kernel_ids: Sequence[KernelId],
        raw: KernelLiveStatBatchResult,
    ) -> dict[KernelId, dict[str, MetricValue] | None]:
        out: dict[KernelId, dict[str, MetricValue] | None] = {}
        for kid in kernel_ids:
            values = raw.by_kernel.get(kid)
            metric_names = cls._metric_names(values) if values is not None else set()
            if not metric_names or values is None:
                out[kid] = None
                continue
            out[kid] = {name: cls._convert_one(values, name) for name in sorted(metric_names)}
        return out

    @staticmethod
    def _metric_names(values: KernelLiveStatValues) -> set[str]:
        return (
            values.instant_current.keys()
            | values.instant_capacity.keys()
            | values.rate_current.keys()
            | values.max.keys()
            | values.rate_max.keys()
            | values.avg.keys()
            | values.rate_avg.keys()
        )

    @staticmethod
    def _convert_one(values: KernelLiveStatValues, name: str) -> MetricValue:
        out = _make_default_metric_value(_resolve_unit_hint(name))

        # `rate_X or X` works because the rate queries only emit rows for
        # cumulative counter metrics (cpu_util/net_rx/net_tx) where the rate-based
        # value is the meaningful one; gauge metrics never appear in rate_*, so
        # the fallback to the raw source is correct by construction.
        current = values.rate_current.get(name) or values.instant_current.get(name)
        capacity = values.instant_capacity.get(name)
        max_value = values.rate_max.get(name) or values.max.get(name)
        avg_value = values.rate_avg.get(name) or values.avg.get(name)

        # Force capacity sentinel for unbounded metrics. The agent may emit a
        # non-null `capacity` sample for these (initialized from `measure.value`),
        # but the value has no meaning as a ceiling, so we always overwrite.
        if current is not None and name in CAPACITY_SENTINEL_METRICS:
            capacity = CAPACITY_SENTINEL

        if current is not None:
            out["current"] = current
        if capacity is not None:
            out["capacity"] = capacity
        if max_value is not None:
            out["stats.max"] = max_value
        if avg_value is not None:
            out["stats.avg"] = avg_value

        if name in _RATE_STAT_METRICS and current is not None:
            out["stats.rate"] = current
        if name in _DIFF_STAT_METRICS and current is not None:
            out["stats.diff"] = current

        try:
            current_value = Decimal(out["current"])
            cap = out["capacity"]
            if cap is None:
                return out
            capacity_value = Decimal(cap)
            if capacity_value > 0:
                out["pct"] = f"{current_value / capacity_value * 100:.2f}"
        except InvalidOperation:
            pass

        return out
