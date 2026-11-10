from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.manager.clients.prometheus.metric_types import ContainerMetricOptionalLabel
from ai.backend.manager.clients.prometheus.types import ValueType
from ai.backend.manager.errors.metric import InvalidContainerMetricName
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.services.metric.actions.container import ContainerMetricAction
from ai.backend.manager.services.metric.service import MetricService

_TIME_RANGE = QueryTimeRange(start="0", end="60", step="1m")
_INVALID_NAME = 'cpu_util"} or vector(1) #'


class TestMetricService:
    @pytest.fixture
    def repository(self) -> MagicMock:
        repository = MagicMock(spec=MetricRepository)
        repository.query_container_metric = AsyncMock(return_value=[])
        return repository

    @pytest.fixture
    def service(self, repository: MagicMock) -> MetricService:
        return MetricService(repository)

    async def test_search_accepts_a_valid_name(
        self, service: MetricService, repository: MagicMock
    ) -> None:
        await service.query_container_metric(
            ContainerMetricAction(
                metric_name="cpu_util",
                labels=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
                time_range=_TIME_RANGE,
            )
        )

        repository.query_container_metric.assert_awaited_once()

    async def test_search_rejects_an_invalid_name(
        self, service: MetricService, repository: MagicMock
    ) -> None:
        with pytest.raises(InvalidContainerMetricName):
            await service.query_container_metric(
                ContainerMetricAction(
                    metric_name=_INVALID_NAME,
                    labels=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
                    time_range=_TIME_RANGE,
                )
            )
        repository.query_container_metric.assert_not_awaited()
