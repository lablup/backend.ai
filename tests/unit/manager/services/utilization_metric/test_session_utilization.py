from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.repositories.metric.types import (
    SessionUtilizationMetricQuery,
    SessionUtilizationMetricResult,
)
from ai.backend.manager.services.metric.actions.session_utilization import (
    SessionUtilizationAction,
    SessionUtilizationObservation,
    SessionUtilizationQuery,
)
from ai.backend.manager.services.metric.service import MetricService

_NOW = datetime(2026, 7, 25, 12, tzinfo=UTC)


class TestQuerySessionUtilization:
    @pytest.fixture()
    def metric_repository(self) -> MagicMock:
        repository = MagicMock(spec=MetricRepository)
        repository.query_session_utilization_metrics = AsyncMock()
        return repository

    @pytest.fixture()
    def service(self, metric_repository: MagicMock) -> MetricService:
        return MetricService(metric_repository)

    async def test_merges_queries_for_the_same_preset(
        self,
        service: MetricService,
        metric_repository: MagicMock,
    ) -> None:
        preset_id = uuid4()
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(
                by_session={
                    first_session_id: Decimal("5"),
                    second_session_id: Decimal("15"),
                }
            )
        )

        result = await service.query_session_utilization(
            SessionUtilizationAction(
                queries=[
                    SessionUtilizationQuery(
                        preset_id=preset_id,
                        session_ids=[first_session_id],
                    ),
                    SessionUtilizationQuery(
                        preset_id=preset_id,
                        session_ids=[first_session_id, second_session_id],
                    ),
                ],
                evaluation_time=_NOW,
            )
        )

        metric_repository.query_session_utilization_metrics.assert_awaited_once_with(
            SessionUtilizationMetricQuery(
                preset_id=preset_id,
                session_ids=[first_session_id, second_session_id],
                evaluation_time=_NOW,
            )
        )
        assert result.observations_by_preset == {
            preset_id: {
                first_session_id: SessionUtilizationObservation(
                    preset_id=preset_id,
                    value=Decimal("5"),
                ),
                second_session_id: SessionUtilizationObservation(
                    preset_id=preset_id,
                    value=Decimal("15"),
                ),
            }
        }

    async def test_partitions_results_by_preset(
        self,
        service: MetricService,
        metric_repository: MagicMock,
    ) -> None:
        first_preset_id = uuid4()
        second_preset_id = uuid4()
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        metric_repository.query_session_utilization_metrics.side_effect = [
            SessionUtilizationMetricResult(
                by_session={first_session_id: Decimal("5")},
            ),
            SessionUtilizationMetricResult(
                by_session={second_session_id: Decimal("15")},
            ),
        ]

        result = await service.query_session_utilization(
            SessionUtilizationAction(
                queries=[
                    SessionUtilizationQuery(
                        preset_id=first_preset_id,
                        session_ids=[first_session_id],
                    ),
                    SessionUtilizationQuery(
                        preset_id=second_preset_id,
                        session_ids=[second_session_id],
                    ),
                ],
                evaluation_time=_NOW,
            )
        )

        assert result.observations_by_preset == {
            first_preset_id: {
                first_session_id: SessionUtilizationObservation(
                    preset_id=first_preset_id,
                    value=Decimal("5"),
                )
            },
            second_preset_id: {
                second_session_id: SessionUtilizationObservation(
                    preset_id=second_preset_id,
                    value=Decimal("15"),
                )
            },
        }

    async def test_missing_metric_value_returns_no_observation(
        self,
        service: MetricService,
        metric_repository: MagicMock,
    ) -> None:
        preset_id = uuid4()
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(by_session={})
        )

        result = await service.query_session_utilization(
            SessionUtilizationAction(
                queries=[
                    SessionUtilizationQuery(
                        preset_id=preset_id,
                        session_ids=[SessionId(uuid4())],
                    )
                ],
                evaluation_time=_NOW,
            )
        )

        assert result.observations_by_preset == {preset_id: {}}

    async def test_empty_queries_skip_repository(
        self,
        service: MetricService,
        metric_repository: MagicMock,
    ) -> None:
        result = await service.query_session_utilization(
            SessionUtilizationAction(queries=[], evaluation_time=_NOW)
        )

        assert result.observations_by_preset == {}
        metric_repository.query_session_utilization_metrics.assert_not_awaited()
