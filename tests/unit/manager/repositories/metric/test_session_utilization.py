from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
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
from ai.backend.manager.clients.prometheus.preset import LabelMatcher, MetricPreset
from ai.backend.manager.data.idle_checker.types import SessionUtilizationQuery
from ai.backend.manager.data.prometheus_query_preset.types import (
    PrometheusQueryPresetData,
    PrometheusQueryPresetListResult,
)
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


def _query(
    preset_id: PrometheusQueryPresetID,
    filter_labels: dict[str, str] | None = None,
    group_labels: tuple[str, ...] = ("session_id",),
) -> SessionUtilizationQuery:
    return SessionUtilizationQuery(
        preset_id=preset_id,
        filter_labels=tuple(sorted((filter_labels or {}).items())),
        group_labels=group_labels,
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
                'avg by ({group_by}) (backendai_container_utilization{{value_type="current",'
                "{labels}}})"
            ),
            time_window="5m",
            filter_labels=["session_id", "container_metric_name"],
            group_labels=["session_id", "device", "project_id"],
            created_at=now,
            updated_at=now,
        )

    @pytest.fixture()
    def prometheus_client(self) -> MagicMock:
        client = MagicMock(spec=PrometheusClient)
        client.execute_preset = AsyncMock()
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
                default_timewindow="30s",
            )

    async def test_queries_stored_preset_with_spec_labels(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        query = _query(
            PrometheusQueryPresetID(preset.id),
            filter_labels={"container_metric_name": "cpu_used"},
        )
        session_id = SessionId(uuid4())
        prometheus_client.execute_preset.return_value = _response([(str(session_id), "9.9")])

        result = await repository.query_session_utilization_metrics(
            {query: [session_id]},
            _EVALUATION_TIME,
        )

        assert result == {query: {session_id: Decimal("9.9")}}
        preset_db_source.search.assert_awaited_once()
        prometheus_client.execute_preset.assert_awaited_once_with(
            MetricPreset(
                template=preset.query_template,
                labels={
                    "container_metric_name": LabelMatcher.exact("cpu_used"),
                    "session_id": LabelMatcher.regex(str(session_id)),
                },
                group_by={"session_id"},
                window="5m",
            ),
            time_range=None,
            time=_EVALUATION_TIME.isoformat(),
        )

    async def test_window_falls_back_to_server_default(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        preset_db_source.search.return_value = _preset_result(replace(preset, time_window=None))
        query = _query(PrometheusQueryPresetID(preset.id))
        prometheus_client.execute_preset.return_value = _response([])

        await repository.query_session_utilization_metrics(
            {query: [SessionId(uuid4())]},
            _EVALUATION_TIME,
        )

        sent_preset = prometheus_client.execute_preset.await_args.args[0]
        assert sent_preset.window == "30s"

    async def test_scopes_query_to_deduplicated_session_batch(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        query = _query(PrometheusQueryPresetID(preset.id))
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        prometheus_client.execute_preset.return_value = _response([])

        await repository.query_session_utilization_metrics(
            {query: [first_session_id, second_session_id, first_session_id]},
            _EVALUATION_TIME,
        )

        sent_labels = prometheus_client.execute_preset.await_args.args[0].labels
        assert sent_labels["session_id"] == LabelMatcher.regex(
            f"{first_session_id}|{second_session_id}"
        )

    async def test_no_session_scope_without_session_id_grouping(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        query = _query(PrometheusQueryPresetID(preset.id), group_labels=("project_id",))
        prometheus_client.execute_preset.return_value = _response([])

        await repository.query_session_utilization_metrics(
            {query: [SessionId(uuid4())]},
            _EVALUATION_TIME,
        )

        sent_labels = prometheus_client.execute_preset.await_args.args[0].labels
        assert "session_id" not in sent_labels

    async def test_user_session_id_filter_is_not_overridden(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        pinned_session_id = str(SessionId(uuid4()))
        query = _query(
            PrometheusQueryPresetID(preset.id),
            filter_labels={"session_id": pinned_session_id},
        )
        prometheus_client.execute_preset.return_value = _response([])

        await repository.query_session_utilization_metrics(
            {query: [SessionId(uuid4())]},
            _EVALUATION_TIME,
        )

        sent_labels = prometheus_client.execute_preset.await_args.args[0].labels
        assert sent_labels["session_id"] == LabelMatcher.exact(pinned_session_id)

    async def test_partitions_results_by_query(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        second_preset = replace(
            preset,
            id=uuid4(),
            name="session-memory-utilization",
            metric_name="mem",
        )
        first_query = _query(PrometheusQueryPresetID(preset.id))
        second_query = _query(PrometheusQueryPresetID(second_preset.id))
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        preset_db_source.search.return_value = _preset_result(preset, second_preset)
        prometheus_client.execute_preset.side_effect = [
            _response([(str(first_session_id), "5")]),
            _response([(str(second_session_id), "15")]),
        ]

        result = await repository.query_session_utilization_metrics(
            {
                first_query: [first_session_id],
                second_query: [second_session_id],
            },
            _EVALUATION_TIME,
        )

        assert result == {
            first_query: {first_session_id: Decimal("5")},
            second_query: {second_session_id: Decimal("15")},
        }
        preset_db_source.search.assert_awaited_once()

    async def test_same_preset_with_different_labels_queried_separately(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        cpu_query = _query(
            PrometheusQueryPresetID(preset.id),
            filter_labels={"container_metric_name": "cpu_used"},
        )
        mem_query = _query(
            PrometheusQueryPresetID(preset.id),
            filter_labels={"container_metric_name": "mem"},
        )
        session_id = SessionId(uuid4())
        prometheus_client.execute_preset.side_effect = [
            _response([(str(session_id), "5")]),
            _response([(str(session_id), "15")]),
        ]

        result = await repository.query_session_utilization_metrics(
            {
                cpu_query: [session_id],
                mem_query: [session_id],
            },
            _EVALUATION_TIME,
        )

        assert result == {
            cpu_query: {session_id: Decimal("5")},
            mem_query: {session_id: Decimal("15")},
        }
        assert prometheus_client.execute_preset.await_count == 2

    async def test_missing_preset_does_not_fail_other_queries(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        query = _query(PrometheusQueryPresetID(preset.id))
        missing_query = _query(PrometheusQueryPresetID(uuid4()))
        session_id = SessionId(uuid4())
        preset_db_source.search.return_value = _preset_result(preset)
        prometheus_client.execute_preset.return_value = _response([(str(session_id), "5")])

        result = await repository.query_session_utilization_metrics(
            {
                query: [session_id],
                missing_query: [SessionId(uuid4())],
            },
            _EVALUATION_TIME,
        )

        assert result == {
            query: {session_id: Decimal("5")},
            missing_query: {},
        }
        assert "Prometheus query preset not found; skipping utilization query" in caplog.text
        assert str(missing_query.preset_id) in caplog.text
        prometheus_client.execute_preset.assert_awaited_once()

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
        query = _query(PrometheusQueryPresetID(preset.id))
        prometheus_client.execute_preset.side_effect = error

        result = await repository.query_session_utilization_metrics(
            {query: [SessionId(uuid4())]},
            _EVALUATION_TIME,
        )

        assert result == {query: {}}

    async def test_skips_malformed_and_non_finite_values(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        query = _query(PrometheusQueryPresetID(preset.id))
        session_id = SessionId(uuid4())
        other_session_id = SessionId(uuid4())
        prometheus_client.execute_preset.return_value = _response([
            ("not-a-uuid", "1"),
            (str(SessionId(uuid4())), "not-a-number"),
            (str(SessionId(uuid4())), "NaN"),
            (str(other_session_id), "99"),
            (str(session_id), "5"),
        ])

        result = await repository.query_session_utilization_metrics(
            {query: [session_id]},
            _EVALUATION_TIME,
        )

        assert result == {query: {session_id: Decimal("5")}}

    async def test_multiple_series_per_session_fold_to_max(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        query = _query(
            PrometheusQueryPresetID(preset.id),
            group_labels=("session_id", "device"),
        )
        session_id = SessionId(uuid4())
        prometheus_client.execute_preset.return_value = _response([
            (str(session_id), "1"),
            (str(session_id), "7"),
            (str(session_id), "2"),
        ])

        result = await repository.query_session_utilization_metrics(
            {query: [session_id]},
            _EVALUATION_TIME,
        )

        assert result == {query: {session_id: Decimal("7")}}

    async def test_no_matching_sessions_logs_warning(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        query = _query(PrometheusQueryPresetID(preset.id), group_labels=("project_id",))
        prometheus_client.execute_preset.return_value = _response([
            (str(SessionId(uuid4())), "5"),
        ])

        result = await repository.query_session_utilization_metrics(
            {query: [SessionId(uuid4())]},
            _EVALUATION_TIME,
        )

        assert result == {query: {}}
        assert "none matched the requested sessions" in caplog.text

    @pytest.mark.parametrize(
        "query_kwargs",
        [
            {"filter_labels": {"unknown_label": "x"}},
            {"group_labels": ("session_id", "unknown_group")},
        ],
    )
    async def test_labels_not_allowed_by_preset_skip_query(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset: PrometheusQueryPresetData,
        caplog: pytest.LogCaptureFixture,
        query_kwargs: dict[str, Any],
    ) -> None:
        query = _query(PrometheusQueryPresetID(preset.id), **query_kwargs)

        result = await repository.query_session_utilization_metrics(
            {query: [SessionId(uuid4())]},
            _EVALUATION_TIME,
        )

        assert result == {query: {}}
        assert "labels not allowed by preset" in caplog.text
        prometheus_client.execute_preset.assert_not_awaited()

    async def test_empty_preset_allow_lists_allow_any_labels(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
        preset: PrometheusQueryPresetData,
    ) -> None:
        preset_db_source.search.return_value = _preset_result(
            replace(preset, filter_labels=[], group_labels=[])
        )
        query = _query(
            PrometheusQueryPresetID(preset.id),
            filter_labels={"anything": "goes"},
            group_labels=("session_id", "any_group"),
        )
        prometheus_client.execute_preset.return_value = _response([])

        await repository.query_session_utilization_metrics(
            {query: [SessionId(uuid4())]},
            _EVALUATION_TIME,
        )

        prometheus_client.execute_preset.assert_awaited_once()

    async def test_empty_queries_skip_data_sources(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
    ) -> None:
        result = await repository.query_session_utilization_metrics({}, _EVALUATION_TIME)

        assert result == {}
        preset_db_source.search.assert_not_awaited()
        prometheus_client.execute_preset.assert_not_awaited()

    async def test_query_without_sessions_skips_data_sources(
        self,
        repository: MetricRepository,
        prometheus_client: MagicMock,
        preset_db_source: MagicMock,
    ) -> None:
        result = await repository.query_session_utilization_metrics(
            {_query(PrometheusQueryPresetID(uuid4())): []},
            _EVALUATION_TIME,
        )

        assert result == {}
        preset_db_source.search.assert_not_awaited()
        prometheus_client.execute_preset.assert_not_awaited()
