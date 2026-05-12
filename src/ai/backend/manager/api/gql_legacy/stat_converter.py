from collections.abc import Iterable
from typing import Final

from ai.backend.common.clients.prometheus.metric_types import KernelLiveStatBatchResult
from ai.backend.common.clients.prometheus.types import MetricValue as PrometheusMetricValue
from ai.backend.common.clients.prometheus.types import ValueType
from ai.backend.common.metrics.types import UTILIZATION_METRIC_INTERVAL
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

    Merge order from upstream is gauge -> diff -> rate, so for
    RATE/DIFF metrics the same `(name, CURRENT)` tuple appears twice;
    `currents[0]` is the raw gauge sample, `currents[-1]` is the
    rate/diff query result.

    `stats.max` / `stats.avg` are not populated
    """

    @classmethod
    def convert(
        cls, result: KernelLiveStatBatchResult
    ) -> dict[KernelId, dict[str, MetricValue] | None]:
        out: dict[KernelId, dict[str, MetricValue] | None] = {}
        for kernel_id, entry in result.entries.items():
            if not entry.values:
                out[kernel_id] = None
                continue
            out[kernel_id] = cls._convert_one_kernel(entry.values)
        return out

    @classmethod
    def _convert_one_kernel(cls, values: Iterable[PrometheusMetricValue]) -> dict[str, MetricValue]:
        grouped: dict[str, list[PrometheusMetricValue]] = {}
        for v in values:
            grouped.setdefault(v.metric_name, []).append(v)

        per_metric: dict[str, MetricValue] = {}
        for name, samples in grouped.items():
            per_metric[name] = cls._convert_metric_samples(name, samples)
        return per_metric

    @staticmethod
    def _convert_metric_samples(
        metric_name: str, samples: list[PrometheusMetricValue]
    ) -> MetricValue:
        # `_resolve_unit_hint` falls back to naming conventions and finally
        # the metric_name itself for unregistered plugin metrics.
        unit_hint = _resolve_unit_hint(metric_name)
        out = _make_default_metric_value(unit_hint=unit_hint)

        currents = [s.value for s in samples if s.value_type is ValueType.CURRENT]
        capacities = [s.value for s in samples if s.value_type is ValueType.CAPACITY]
        pcts = [s.value for s in samples if s.value_type is ValueType.PCT]

        is_rate_metric = metric_name in _RATE_STAT_METRICS
        is_diff_metric = metric_name in _DIFF_STAT_METRICS

        if currents:
            # RATE/DIFF: prefer the rate/diff query result over the raw gauge,
            # mirroring the legacy `current_hook=stats.rate|diff` behavior.
            if (is_rate_metric or is_diff_metric) and len(currents) > 1:
                out["current"] = currents[-1]
            else:
                out["current"] = currents[0]
        if capacities:
            out["capacity"] = capacities[-1]

        if is_rate_metric and currents:
            # RATE template applies `/ UTILIZATION_METRIC_INTERVAL`; undo it
            # here to recover the per-second magnitude legacy `stats.rate` had.
            # TODO: separate the rate query from the gauge query so this
            #       hack-multiply isn't needed.
            try:
                rate_value = float(currents[-1]) * UTILIZATION_METRIC_INTERVAL
                out["stats.rate"] = f"{rate_value:.6f}"
            except ValueError:
                out["stats.rate"] = currents[-1]
        if is_diff_metric and currents:
            # Per-second rate, not the legacy per-5s delta — GQL consumers
            # only read `cpu_util.pct`, so magnitude mismatch is acceptable.
            out["stats.diff"] = currents[-1]

        # Derive pct from current/capacity when no PCT sample was emitted.
        if pcts:
            out["pct"] = pcts[-1]
        else:
            try:
                current_value = float(out["current"])
                capacity = out["capacity"]
                if capacity is None:
                    return out
                capacity_value = float(capacity)
                if capacity_value > 0:
                    out["pct"] = f"{current_value / capacity_value * 100:.2f}"
            except ValueError:
                pass

        return out
