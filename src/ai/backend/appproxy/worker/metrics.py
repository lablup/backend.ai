import asyncio
import logging
from collections import defaultdict
from decimal import Decimal
from typing import Any, Final
from uuid import UUID

import aiohttp
from prometheus_client.parser import text_string_to_metric_families
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline

from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.common import msgpack, redis_helper
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import MetricKey, ModelServiceStatus, RuntimeVariant

from .types import (
    Circuit,
    HistogramMeasurement,
    HistogramMetric,
    InferenceAppInfo,
    InferenceMeasurement,
    Measurement,
    Metric,
    MetricTypes,
    MovingStatistics,
    RootContext,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

CACHE_LIFESPAN: Final[int] = 120


def add_matrices(*ms: tuple[float | int | Decimal, ...]) -> tuple[Decimal, ...]:
    if len(ms) == 0:
        return tuple()
    matrix_size = len(ms[0])
    for m in ms:
        assert len(m) == matrix_size, "Inconsistent matrix size"
    base = [Decimal()] * matrix_size
    for m in ms:
        for i in range(matrix_size):
            base[i] += Decimal(m[i])
    return tuple(base)


async def gather_prometheus_inference_measures(
    routes: list[RouteInfo], request_path="/metrics"
) -> list[InferenceMeasurement]:
    histogram_metrics_labels: dict[str, tuple[str, ...]] = {}  # [metric name: (bucket label, ...)]

    histogram_bucket_metrics: defaultdict[str, dict[UUID, tuple[Decimal, ...]]] = defaultdict(
        dict
    )  # [metric name: [route ID: (bucket, ...)]]
    histogram_count_metrics: defaultdict[str, dict[UUID, int]] = defaultdict(
        dict
    )  # [metric name: [route ID: value]]
    histogram_sum_metrics: defaultdict[str, dict[UUID, Decimal]] = defaultdict(
        dict
    )  # [metric name: [route ID: value]]
    gauge_metrics: defaultdict[str, defaultdict[UUID, Decimal]] = defaultdict(
        lambda: defaultdict(Decimal)
    )  # [metric name: [route ID: value]]
    counter_metrics: defaultdict[str, defaultdict[UUID, Decimal]] = defaultdict(
        lambda: defaultdict(Decimal)
    )  # [metric name: [route ID: value]]

    for route in routes:
        if not route.route_id:
            continue

        # Skip unhealthy routes to avoid connection errors
        if route.health_status and route.health_status != ModelServiceStatus.HEALTHY:
            log.debug("Skipping metrics collection for unhealthy route {}", route.route_id)
            continue
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://{route.kernel_host}:{route.kernel_port}/metrics"
            ) as resp:
                resp.raise_for_status()
                metrics_text = await resp.text()
                metric_families = text_string_to_metric_families(metrics_text)
                for metric_family in metric_families:
                    metric_name = metric_family.name
                    match metric_family.type:
                        case "histogram":
                            labels: list[str] = []
                            values: list[Decimal] = []
                            for sample in metric_family.samples:
                                if sample.name.endswith("_bucket"):
                                    labels.append(sample.labels["le"])
                                    values.append(Decimal(sample.value))
                                elif sample.name.endswith("_count"):
                                    histogram_count_metrics[metric_name][route.route_id] = int(
                                        sample.value
                                    )
                                elif sample.name.endswith("_sum"):
                                    histogram_sum_metrics[metric_name][route.route_id] = Decimal(
                                        sample.value
                                    )
                            histogram_metrics_labels[metric_name] = tuple(labels)
                            histogram_bucket_metrics[metric_name][route.route_id] = tuple(values)
                        case "gauge":
                            gauge_metrics[metric_name][route.route_id] = Decimal(
                                metric_family.samples[0].value
                            )
                        case "counter":
                            counter_metrics[metric_name][route.route_id] = Decimal(
                                metric_family.samples[0].value
                            )

    measures: list[InferenceMeasurement] = []
    for metric_name, per_route_histogram_metrics in histogram_bucket_metrics.items():
        aggregated_buckets = add_matrices(*per_route_histogram_metrics.values())
        aggregated_count = sum([
            d for d in histogram_count_metrics[metric_name].values() if d is not None
        ])
        aggregated_sum = sum([
            d for d in histogram_sum_metrics[metric_name].values() if d is not None
        ]) or Decimal("0")  # sum returns Literal['0'] if empty

        aggregated_histogram_measurement = HistogramMeasurement(
            buckets={
                label: Decimal(value)
                for label, value in zip(histogram_metrics_labels[metric_name], aggregated_buckets)
            },
            count=aggregated_count,
            sum=aggregated_sum,
        )
        per_replica_histogram_measurements = {
            route_id: HistogramMeasurement(
                buckets={
                    label: Decimal(value)
                    for label, value in zip(histogram_metrics_labels[metric_name], values)
                },
                count=count,
                sum=sum,
            )
            for route_id, values, count, sum in zip(
                per_route_histogram_metrics.keys(),
                per_route_histogram_metrics.values(),
                [
                    histogram_count_metrics[metric_name].get(route_id)
                    for route_id in per_route_histogram_metrics.keys()
                ],
                [
                    histogram_sum_metrics[metric_name].get(route_id)
                    for route_id in per_route_histogram_metrics.keys()
                ],
            )
        }
        measures.append(
            InferenceMeasurement(
                key=MetricKey(metric_name),
                type=MetricTypes.HISTOGRAM,
                per_app=aggregated_histogram_measurement,
                per_replica=per_replica_histogram_measurements,
            )
        )
    for metric_name, per_route_gauge_metrics in gauge_metrics.items():
        aggregated_gauge_metric = Measurement(Decimal(sum(per_route_gauge_metrics.values())))
        per_replica_gauge_measurements = {
            route_id: Measurement(value) for route_id, value in per_route_gauge_metrics.items()
        }
        measures.append(
            InferenceMeasurement(
                key=MetricKey(metric_name),
                type=MetricTypes.GAUGE,
                per_app=aggregated_gauge_metric,
                per_replica=per_replica_gauge_measurements,
            )
        )
    for metric_name, per_route_gauge_metrics in counter_metrics.items():
        aggregated_counter_metric = Measurement(Decimal(sum(per_route_gauge_metrics.values())))
        per_replica_gauge_measurements = {
            route_id: Measurement(value) for route_id, value in per_route_gauge_metrics.items()
        }
        measures.append(
            InferenceMeasurement(
                key=MetricKey(metric_name),
                type=MetricTypes.GAUGE,
                per_app=aggregated_counter_metric,
                per_replica=per_replica_gauge_measurements,
            )
        )
    return measures


async def gather_inference_measures(circuit: Circuit) -> list[InferenceMeasurement] | None:
    assert isinstance(circuit.app_info, InferenceAppInfo)
    match circuit.app_info.runtime_variant:
        case RuntimeVariant.VLLM:
            raw_measures = await gather_prometheus_inference_measures(circuit.route_info)

            measures: list[InferenceMeasurement] = []
            for measure in raw_measures:
                if not measure.key.startswith("vllm:"):
                    continue
                measures.append(
                    InferenceMeasurement(
                        key=MetricKey(measure.key.replace("vllm:", "vllm_")),
                        type=MetricTypes.GAUGE,
                        per_app=measure.per_app,
                        per_replica=measure.per_replica,
                    )
                )
            return measures
        case RuntimeVariant.HUGGINGFACE_TGI:
            return await gather_prometheus_inference_measures(circuit.route_info)
        case _:
            return None


async def collect_inference_metric(root_ctx: RootContext, interval: float) -> None:
    try:
        inference_circuits = [
            circuit
            for circuit in root_ctx.proxy_frontend.circuits.values()
            if isinstance(circuit.app_info, InferenceAppInfo)
        ]

        # Here we use asyncio.gather() instead of aiotools.TaskGroup
        # to keep methods of other plugins running when a plugin raises an error
        # instead of cancelling them.
        _tasks: list[asyncio.Task[list[InferenceMeasurement] | None]] = [
            asyncio.create_task(gather_inference_measures(c)) for c in inference_circuits
        ]

        results = await asyncio.gather(*_tasks, return_exceptions=True)
        for circuit, result in zip(inference_circuits, results):
            if not result:  # Unsupported runtime variant (custom, Triton, ...)
                continue
            if isinstance(result, BaseException):
                log.error(
                    "collect_inference_metric(): gather_inference_measures() error", exc_info=result
                )
                continue
            for inference_measure in result:
                metric_key = inference_measure.key
                # update per-app metric
                if metric_key not in circuit._app_inference_metrics:
                    match inference_measure.per_app:
                        case Measurement():
                            circuit._app_inference_metrics[metric_key] = Metric(
                                metric_key,
                                inference_measure.type,
                                current=inference_measure.per_app.value,
                                capacity=inference_measure.per_app.capacity,
                                unit_hint=inference_measure.unit_hint,
                                stats=MovingStatistics(inference_measure.per_app.value),
                                stats_filter=frozenset(inference_measure.stats_filter),
                            )
                        case HistogramMeasurement():
                            circuit._app_inference_metrics[metric_key] = HistogramMetric(
                                metric_key,
                                "le",  # FIXME: customize
                                buckets=inference_measure.per_app.buckets,
                                count=inference_measure.per_app.count,
                                sum=inference_measure.per_app.sum,
                            )
                else:
                    existing_metric = circuit._app_inference_metrics[metric_key]
                    match inference_measure.per_app:
                        case Measurement():
                            if not isinstance(existing_metric, Metric):
                                raise ValueError(
                                    f"Unexpected metric type: {type(existing_metric)}, expected Metric"
                                )
                            existing_metric.update(inference_measure.per_app)
                        case HistogramMeasurement():
                            if not isinstance(existing_metric, HistogramMetric):
                                raise ValueError(
                                    f"Unexpected metric type: {type(existing_metric)}, expected HistogramMetric"
                                )
                            existing_metric.update(
                                inference_measure.per_app.buckets,
                                count=inference_measure.per_app.count,
                                sum=inference_measure.per_app.sum,
                            )
                # update per-replica metric
                for route_id, replica_inference_metrics in inference_measure.per_replica.items():
                    if metric_key not in circuit._replica_inference_metrics:
                        circuit._replica_inference_metrics[metric_key] = {}
                    if route_id not in circuit._replica_inference_metrics[metric_key]:
                        match replica_inference_metrics:
                            case Measurement():
                                circuit._replica_inference_metrics[metric_key][route_id] = Metric(
                                    metric_key,
                                    inference_measure.type,
                                    current=replica_inference_metrics.value,
                                    capacity=replica_inference_metrics.capacity,
                                    unit_hint=inference_measure.unit_hint,
                                    stats=MovingStatistics(replica_inference_metrics.value),
                                    stats_filter=frozenset(inference_measure.stats_filter),
                                )
                            case HistogramMeasurement():
                                circuit._replica_inference_metrics[metric_key][route_id] = (
                                    HistogramMetric(
                                        metric_key,
                                        "le",  # FIXME: customize
                                        buckets=replica_inference_metrics.buckets,
                                        count=replica_inference_metrics.count,
                                        sum=replica_inference_metrics.sum,
                                    )
                                )
                    else:
                        existing_metric = circuit._replica_inference_metrics[metric_key][route_id]
                        match replica_inference_metrics:
                            case Measurement():
                                if not isinstance(existing_metric, Metric):
                                    raise ValueError(
                                        f"Unexpected metric type: {type(existing_metric)}, expected Metric"
                                    )
                                existing_metric.update(replica_inference_metrics)
                            case HistogramMeasurement():
                                if not isinstance(existing_metric, HistogramMetric):
                                    raise ValueError(
                                        f"Unexpected metric type: {type(existing_metric)}, expected HistogramMetric"
                                    )
                                existing_metric.update(
                                    replica_inference_metrics.buckets,
                                    count=replica_inference_metrics.count,
                                    sum=replica_inference_metrics.sum,
                                )

        # push to the Redis server
        app_metrics_updates = {
            circuit.endpoint_id: {
                key: obj.to_serializable_dict()
                for key, obj in circuit._app_inference_metrics.items()
            }
            for circuit in inference_circuits
            if circuit._app_inference_metrics and circuit.endpoint_id
        }
        replica_metrics_updates: dict[tuple[UUID, UUID], Any] = {}

        for circuit in inference_circuits:
            if not circuit._replica_inference_metrics or not circuit.endpoint_id:
                continue
            for key, metric_pair in circuit._replica_inference_metrics.items():
                for route_id, obj in metric_pair.items():
                    if (circuit.endpoint_id, route_id) not in replica_metrics_updates:
                        replica_metrics_updates[(circuit.endpoint_id, route_id)] = {}
                    replica_metrics_updates[(circuit.endpoint_id, route_id)][key] = (
                        obj.to_serializable_dict()
                    )

        if root_ctx.local_config.debug.log_stats:
            log.debug(
                "stats: app_updates: {}",
                app_metrics_updates,
            )
            log.debug(
                "stats: replica_updates: {}",
                replica_metrics_updates,
            )

        async def _pipe_builder(r: Redis) -> Pipeline:
            pipe = r.pipeline()
            for endpoint_id, app_measures in app_metrics_updates.items():
                await pipe.set(f"inference.{endpoint_id}.app", msgpack.packb(app_measures))
                await pipe.expire(f"inference.{endpoint_id}.app", CACHE_LIFESPAN)
            for (endpoint_id, replica_id), replica_measures in replica_metrics_updates.items():
                await pipe.set(
                    f"inference.{endpoint_id}.replica.{replica_id}", msgpack.packb(replica_measures)
                )
                await pipe.expire(f"inference.{endpoint_id}.replica.{replica_id}", CACHE_LIFESPAN)
            return pipe

        await redis_helper.execute(root_ctx.redis_stat, _pipe_builder)
    except Exception:
        log.exception("collect_inference_metrics(): error while collecting metric:")
        raise
