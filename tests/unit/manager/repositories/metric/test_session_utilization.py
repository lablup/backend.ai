from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ai.backend.common.dto.clients.prometheus.response import PrometheusResponse
from ai.backend.common.exception import (
    InvalidMetricPresetTemplate,
    PrometheusConnectionError,
)
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.types import SessionId
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.data.prometheus_query_preset.types import (
    PrometheusQueryPresetData,
    PrometheusQueryPresetListResult,
)
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.repositories.metric.repository import MetricRepository
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


def _preset_result(
    *presets: PrometheusQueryPresetData,
) -> PrometheusQueryPresetListResult:
    return PrometheusQueryPresetListResult(
        items=list(presets),
        total_count=len(presets),
        has_next_page=False,
        has_previous_page=False,
    )


class TestSessionUtilizationMetrics:
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
        source.search = AsyncMock(return_value=_preset_result(preset))
        return source

    @pytest.fixture()
    def repository(
        self,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
    ) -> MetricRepository:
        with patch(
            "ai.backend.manager.repositories.metric.repository.PrometheusQueryPresetDBSource",
            return_value=preset_db_source,
        ):
            return MetricRepository(
                db=MagicMock(),
                prometheus_client=prometheus_client,
            )

    async def test_queries_stored_preset(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        preset_id = PrometheusQueryPresetID(preset.id)
        session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            (str(session_id), "9.9")
        ])

        result = await repository.query_session_utilization_metrics(
            {preset_id: [session_id]},
            _EVALUATION_TIME,
        )

        assert result == {preset_id: {session_id: Decimal("9.9")}}
        preset_db_source.search.assert_awaited_once()
        prometheus_client.fetch_session_utilization.assert_awaited_once_with(
            query_template=preset.query_template,
            time_window="5m",
            session_ids=[session_id],
            evaluation_time=_EVALUATION_TIME.isoformat(),
        )

    async def test_queries_all_sessions_for_preset(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        preset_id = PrometheusQueryPresetID(preset.id)
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            (str(first_session_id), "5"),
            (str(second_session_id), "15"),
        ])

        result = await repository.query_session_utilization_metrics(
            {preset_id: [first_session_id, second_session_id]},
            _EVALUATION_TIME,
        )

        assert result == {
            preset_id: {
                first_session_id: Decimal("5"),
                second_session_id: Decimal("15"),
            }
        }
        preset_db_source.search.assert_awaited_once()
        prometheus_client.fetch_session_utilization.assert_awaited_once_with(
            query_template=preset.query_template,
            time_window=preset.time_window,
            session_ids=[first_session_id, second_session_id],
            evaluation_time=_EVALUATION_TIME.isoformat(),
        )

    async def test_partitions_results_by_preset(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        first_preset_id = PrometheusQueryPresetID(preset.id)
        second_preset = replace(
            preset,
            id=uuid4(),
            name="session-memory-utilization",
            metric_name="mem",
        )
        second_preset_id = PrometheusQueryPresetID(second_preset.id)
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        preset_db_source.search.return_value = _preset_result(preset, second_preset)
        prometheus_client.fetch_session_utilization.side_effect = [
            _response([(str(first_session_id), "5")]),
            _response([(str(second_session_id), "15")]),
        ]

        result = await repository.query_session_utilization_metrics(
            {
                first_preset_id: [first_session_id],
                second_preset_id: [second_session_id],
            },
            _EVALUATION_TIME,
        )

        assert result == {
            first_preset_id: {first_session_id: Decimal("5")},
            second_preset_id: {second_session_id: Decimal("15")},
        }
        preset_db_source.search.assert_awaited_once()

    async def test_missing_preset_does_not_fail_other_queries(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        preset_id = PrometheusQueryPresetID(preset.id)
        missing_preset_id = PrometheusQueryPresetID(uuid4())
        session_id = SessionId(uuid4())
        preset_db_source.search.return_value = _preset_result(preset)
        prometheus_client.fetch_session_utilization.return_value = _response([
            (str(session_id), "5")
        ])

        result = await repository.query_session_utilization_metrics(
            {
                preset_id: [session_id],
                missing_preset_id: [SessionId(uuid4())],
            },
            _EVALUATION_TIME,
        )

        assert result == {
            preset_id: {session_id: Decimal("5")},
            missing_preset_id: {},
        }
        assert "Prometheus query preset not found; skipping utilization query" in caplog.text
        assert str(missing_preset_id) in caplog.text
        prometheus_client.fetch_session_utilization.assert_awaited_once()

    @pytest.mark.parametrize(
        "error",
        [
            PrometheusConnectionError("unavailable"),
            InvalidMetricPresetTemplate("failed to render template"),
        ],
    )
    async def test_failed_query_returns_empty_session_mapping(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
        error: Exception,
    ) -> None:
        preset_id = PrometheusQueryPresetID(preset.id)
        prometheus_client.fetch_session_utilization.side_effect = error

        result = await repository.query_session_utilization_metrics(
            {preset_id: [SessionId(uuid4())]},
            _EVALUATION_TIME,
        )

        assert result == {preset_id: {}}

    async def test_missing_metric_value_returns_empty_session_mapping(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        preset_id = PrometheusQueryPresetID(preset.id)
        prometheus_client.fetch_session_utilization.return_value = _response([])

        result = await repository.query_session_utilization_metrics(
            {preset_id: [SessionId(uuid4())]},
            _EVALUATION_TIME,
        )

        assert result == {preset_id: {}}

    async def test_skips_malformed_and_non_finite_values(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        preset_id = PrometheusQueryPresetID(preset.id)
        session_id = SessionId(uuid4())
        other_session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            ("not-a-uuid", "1"),
            (str(SessionId(uuid4())), "not-a-number"),
            (str(SessionId(uuid4())), "NaN"),
            (str(other_session_id), "99"),
            (str(session_id), "5"),
        ])

        result = await repository.query_session_utilization_metrics(
            {preset_id: [session_id]},
            _EVALUATION_TIME,
        )

        assert result == {preset_id: {session_id: Decimal("5")}}

    async def test_duplicate_session_values_raise_internal_error(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        preset_id = PrometheusQueryPresetID(preset.id)
        session_id = SessionId(uuid4())
        prometheus_client.fetch_session_utilization.return_value = _response([
            (str(session_id), "1"),
            (str(session_id), "2"),
        ])

        with pytest.raises(InternalServerError):
            await repository.query_session_utilization_metrics(
                {preset_id: [session_id]},
                _EVALUATION_TIME,
            )

    async def test_empty_queries_skip_data_sources(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
    ) -> None:
        result = await repository.query_session_utilization_metrics({}, _EVALUATION_TIME)

        assert result == {}
        preset_db_source.search.assert_not_awaited()
        prometheus_client.fetch_session_utilization.assert_not_awaited()

    async def test_query_without_sessions_skips_data_sources(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
    ) -> None:
        result = await repository.query_session_utilization_metrics(
            {PrometheusQueryPresetID(uuid4()): []},
            _EVALUATION_TIME,
        )

        assert result == {}
        preset_db_source.search.assert_not_awaited()
        prometheus_client.fetch_session_utilization.assert_not_awaited()
