import asyncio
import uuid

import pytest
from prometheus_client import REGISTRY, generate_latest

from ai.backend.agent.metrics.metric import UtilizationMetricObserver
from ai.backend.agent.metrics.types import (
    CAPACITY_METRIC_KEY,
    CURRENT_METRIC_KEY,
    FlattenedKernelMetric,
)
from ai.backend.agent.stats import Metric
from ai.backend.common.types import AgentId, KernelId, MetricKey, SessionId


@pytest.fixture
def observer() -> UtilizationMetricObserver:
    return UtilizationMetricObserver.instance()


@pytest.fixture
def kernel_metric() -> FlattenedKernelMetric:
    return FlattenedKernelMetric(
        agent_id=AgentId("agent-1"),
        kernel_id=KernelId(uuid.UUID("08ff18f9-e263-47b6-a0aa-d97f8ddfbd5b")),
        session_id=SessionId(uuid.UUID("889e0d78-75a2-4c81-950e-159431e84c52")),
        owner_user_id=uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        project_id=None,
        key=MetricKey("mem"),
        value_pairs=[
            (CURRENT_METRIC_KEY, "1073741824"),
            (CAPACITY_METRIC_KEY, "8589934592"),
        ],
    )


class TestUtilizationMetricObserver:
    def test_observe_container_metric_exports_series(
        self,
        observer: UtilizationMetricObserver,
        kernel_metric: FlattenedKernelMetric,
    ) -> None:
        observer.observe_container_metric(metric=kernel_metric)

        exposition = generate_latest(REGISTRY).decode("utf-8")
        assert 'kernel_id="08ff18f9-e263-47b6-a0aa-d97f8ddfbd5b"' in exposition
        assert 'value_type="capacity"' in exposition
        assert "8.589934592e+09" in exposition
        # None ownership labels are exported as "undefined"
        assert 'project_id="undefined"' in exposition

    async def test_lazy_remove_container_metric_removes_series(
        self,
        observer: UtilizationMetricObserver,
        kernel_metric: FlattenedKernelMetric,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "ai.backend.agent.metrics.metric.UTILIZATION_METRIC_DETENTION",
            0.0,
        )
        observer.observe_container_metric(metric=kernel_metric)
        kernel_metrics: dict[KernelId, dict[MetricKey, Metric]] = {kernel_metric.kernel_id: {}}

        await observer.lazy_remove_container_metric(
            kernel_metrics,
            agent_id=kernel_metric.agent_id,
            kernel_id=kernel_metric.kernel_id,
            session_id=kernel_metric.session_id,
            owner_user_id=kernel_metric.owner_user_id,
            project_id=kernel_metric.project_id,
            keys=[kernel_metric.key],
        )
        await observer._removal_kernel_tasks[kernel_metric.kernel_id]
        # Let the task's done-callback (which prunes the local caches) run.
        await asyncio.sleep(0)

        exposition = generate_latest(REGISTRY).decode("utf-8")
        assert 'kernel_id="08ff18f9-e263-47b6-a0aa-d97f8ddfbd5b"' not in exposition
        assert kernel_metric.kernel_id not in kernel_metrics
