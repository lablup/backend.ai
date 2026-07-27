from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.idle_checker.types import UtilizationKernelPolicy
from ai.backend.common.dto.clients.prometheus.response import PrometheusResponse
from ai.backend.common.exception import PrometheusConnectionError
from ai.backend.common.types import SessionId
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.data.metric.types import SessionUtilizationMetricResult
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.repositories.metric.types import SessionUtilizationMetricQuery

_EVALUATION_TIME = datetime(2026, 7, 25, 12, tzinfo=UTC)


def _response(values: list[tuple[str, str]]) -> PrometheusResponse:
    return PrometheusResponse.model_validate({
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"session_id": session_id},
                    "value": [0, value],
                }
                for session_id, value in values
            ],
        },
    })


def _query(session_id: SessionId) -> SessionUtilizationMetricQuery:
    return SessionUtilizationMetricQuery(
        metric_name="cpu_util",
        kernel_policy=UtilizationKernelPolicy.AVERAGE,
        time_window_seconds=None,
        session_ids=(session_id,),
        evaluation_time=_EVALUATION_TIME,
    )


class TestQuerySessionUtilizationMetrics:
    @pytest.fixture
    def prometheus_client(self) -> MagicMock:
        client = MagicMock(spec=PrometheusClient)
        client.fetch_session_utilization = AsyncMock()
        return client

    @pytest.fixture
    def repository(self, prometheus_client: MagicMock) -> MetricRepository:
        return MetricRepository(MagicMock(), prometheus_client)

    async def test_returns_values_by_query_and_session(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
    ) -> None:
        session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            (str(session_id), "9.9")
        ])

        result = await repository.query_session_utilization_metrics(_query(session_id))

        assert result == SessionUtilizationMetricResult(by_session={session_id: Decimal("9.9")})
        prometheus_client.fetch_session_utilization.assert_awaited_once_with(
            metric_name="cpu_util",
            kernel_policy=UtilizationKernelPolicy.AVERAGE,
            time_window_seconds=None,
            session_ids=(session_id,),
            evaluation_time=_EVALUATION_TIME.isoformat(),
        )

    async def test_failed_query_returns_unknown(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
    ) -> None:
        session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.side_effect = PrometheusConnectionError(
            "unavailable"
        )

        result = await repository.query_session_utilization_metrics(_query(session_id))

        assert result == SessionUtilizationMetricResult(by_session={})

    async def test_skips_malformed_and_non_finite_values(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
    ) -> None:
        session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            ("not-a-uuid", "1"),
            (str(SessionId(uuid4())), "not-a-number"),
            (str(SessionId(uuid4())), "NaN"),
            (str(session_id), "5"),
        ])

        result = await repository.query_session_utilization_metrics(_query(session_id))

        assert result == SessionUtilizationMetricResult(by_session={session_id: Decimal("5")})

    async def test_duplicate_session_values_raise_internal_error(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
    ) -> None:
        session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            (str(session_id), "1"),
            (str(session_id), "2"),
        ])

        with pytest.raises(InternalServerError):
            await repository.query_session_utilization_metrics(_query(session_id))
