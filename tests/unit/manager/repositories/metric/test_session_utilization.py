from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.dto.clients.prometheus.response import PrometheusResponse
from ai.backend.common.exception import InvalidMetricPresetTemplate, PrometheusConnectionError
from ai.backend.common.types import SessionId
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.repositories.metric.types import (
    SessionUtilizationMetricQuery,
    SessionUtilizationMetricResult,
)
from ai.backend.manager.repositories.prometheus_query_preset.db_source import (
    PrometheusQueryPresetDBSource,
)

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


class TestQuerySessionUtilizationMetrics:
    @pytest.fixture()
    def preset(self) -> PrometheusQueryPresetData:
        now = datetime.now(tz=UTC)
        return PrometheusQueryPresetData(
            id=uuid4(),
            name="session-cpu-utilization",
            description=None,
            rank=0,
            category_id=None,
            metric_name="cpu_used",
            query_template=(
                'avg by (session_id) (backendai_container_utilization{{value_type="current",'
                'container_metric_name="cpu_used",{labels}}})'
            ),
            time_window="5m",
            filter_labels=["session_id"],
            group_labels=[],
            created_at=now,
            updated_at=now,
        )

    @pytest.fixture()
    def prometheus_client(self) -> MagicMock:
        client = MagicMock(spec=PrometheusClient)
        client.fetch_session_utilization = AsyncMock()
        return client

    @pytest.fixture()
    def preset_db_source(self, preset: PrometheusQueryPresetData) -> MagicMock:
        source = MagicMock(spec=PrometheusQueryPresetDBSource)
        source.get_by_id = AsyncMock(return_value=preset)
        return source

    @pytest.fixture()
    def repository(
        self,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
    ) -> MetricRepository:
        return MetricRepository(
            prometheus_client=prometheus_client,
            prometheus_query_preset_db_source=preset_db_source,
        )

    def _query(
        self,
        preset: PrometheusQueryPresetData,
        session_id: SessionId,
    ) -> SessionUtilizationMetricQuery:
        return SessionUtilizationMetricQuery(
            preset_id=preset.id,
            session_ids=(session_id,),
            evaluation_time=_EVALUATION_TIME,
        )

    async def test_queries_stored_preset(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            (str(session_id), "9.9")
        ])

        result = await repository.query_session_utilization_metrics(self._query(preset, session_id))

        assert result == SessionUtilizationMetricResult(by_session={session_id: Decimal("9.9")})
        preset_db_source.get_by_id.assert_awaited_once_with(preset.id)
        prometheus_client.fetch_session_utilization.assert_awaited_once_with(
            query_template=preset.query_template,
            time_window="5m",
            session_ids=(session_id,),
            evaluation_time=_EVALUATION_TIME.isoformat(),
        )

    @pytest.mark.parametrize(
        "error",
        [
            PrometheusConnectionError("unavailable"),
            InvalidMetricPresetTemplate("failed to render template"),
        ],
    )
    async def test_failed_query_returns_unknown(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
        error: Exception,
    ) -> None:
        session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.side_effect = error

        result = await repository.query_session_utilization_metrics(self._query(preset, session_id))

        assert result == SessionUtilizationMetricResult(by_session={})

    async def test_skips_malformed_and_non_finite_values(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        session_id = SessionId(uuid4())
        other_session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            ("not-a-uuid", "1"),
            (str(SessionId(uuid4())), "not-a-number"),
            (str(SessionId(uuid4())), "NaN"),
            (str(other_session_id), "99"),
            (str(session_id), "5"),
        ])

        result = await repository.query_session_utilization_metrics(self._query(preset, session_id))

        assert result == SessionUtilizationMetricResult(by_session={session_id: Decimal("5")})

    async def test_duplicate_session_values_raise_internal_error(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            (str(session_id), "1"),
            (str(session_id), "2"),
        ])

        with pytest.raises(InternalServerError):
            await repository.query_session_utilization_metrics(self._query(preset, session_id))
