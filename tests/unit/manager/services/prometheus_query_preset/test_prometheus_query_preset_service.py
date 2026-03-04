"""
Tests for PrometheusQueryPresetService functionality.
Tests the service layer with mocked repository and prometheus client.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import (
    PrometheusQueryData,
    PrometheusQueryRangeResponse,
)
from ai.backend.common.exception import (
    PrometheusQueryPresetInvalidLabel,
    PrometheusQueryPresetNotFound,
)
from ai.backend.manager.data.prometheus_query_preset import (
    ExecutePresetOptions,
    PrometheusQueryPresetData,
    PrometheusQueryPresetListResult,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.prometheus_query_preset import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.prometheus_query_preset.actions import (
    CreatePresetAction,
    DeletePresetAction,
    ExecutePresetAction,
    GetPresetAction,
    ModifyPresetAction,
    SearchPresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)


class TestPrometheusQueryPresetService:
    @pytest.fixture
    def preset_data(self) -> PrometheusQueryPresetData:
        now = datetime.now(UTC)
        return PrometheusQueryPresetData(
            id=uuid4(),
            name="cpu_usage",
            metric_name="backendai_container_cpu_util",
            query_template="rate(container_cpu_usage_seconds_total{{{labels}}}[{window}])",
            time_window="5m",
            filter_labels=["kernel_id", "session_id"],
            group_labels=["kernel_id"],
            created_at=now,
            updated_at=now,
        )

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=PrometheusQueryPresetRepository)

    @pytest.fixture
    def mock_prometheus_client(self) -> MagicMock:
        return MagicMock(spec=PrometheusClient)

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_prometheus_client: MagicMock,
    ) -> PrometheusQueryPresetService:
        return PrometheusQueryPresetService(
            repository=mock_repository,
            prometheus_client=mock_prometheus_client,
            default_timewindow="1m",
        )

    async def test_create_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        mock_repository.create = AsyncMock(return_value=preset_data)

        creator = MagicMock(spec=Creator)
        action = CreatePresetAction(creator=creator)
        result = await service.create_preset(action)

        assert result.preset == preset_data
        mock_repository.create.assert_called_once_with(creator)

    async def test_get_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        action = GetPresetAction(preset_id=preset_data.id)
        result = await service.get_preset(action)

        assert result.preset == preset_data
        mock_repository.get_by_id.assert_called_once_with(preset_data.id)

    async def test_get_preset_not_found(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_id = uuid4()
        mock_repository.get_by_id = AsyncMock(
            side_effect=PrometheusQueryPresetNotFound(f"Preset {preset_id} not found")
        )

        action = GetPresetAction(preset_id=preset_id)
        with pytest.raises(PrometheusQueryPresetNotFound):
            await service.get_preset(action)

    async def test_search_presets(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        mock_repository.search = AsyncMock(
            return_value=PrometheusQueryPresetListResult(
                items=[preset_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchPresetsAction(querier=querier)
        result = await service.search_presets(action)

        assert result.items == [preset_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search.assert_called_once_with(querier)

    async def test_search_presets_empty(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.search = AsyncMock(
            return_value=PrometheusQueryPresetListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchPresetsAction(querier=querier)
        result = await service.search_presets(action)

        assert result.items == []
        assert result.total_count == 0

    async def test_modify_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        mock_repository.update = AsyncMock(return_value=preset_data)

        updater = MagicMock(spec=Updater)
        action = ModifyPresetAction(preset_id=preset_data.id, updater=updater)
        result = await service.modify_preset(action)

        assert result.preset == preset_data
        mock_repository.update.assert_called_once_with(updater)

    async def test_delete_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_id = uuid4()
        mock_repository.delete = AsyncMock(return_value=True)

        action = DeletePresetAction(preset_id=preset_id)
        result = await service.delete_preset(action)

        assert result.preset_id == preset_id
        mock_repository.delete.assert_called_once_with(preset_id)

    async def test_delete_preset_not_found(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_id = uuid4()
        mock_repository.delete = AsyncMock(
            side_effect=PrometheusQueryPresetNotFound(f"Preset {preset_id} not found")
        )

        action = DeletePresetAction(preset_id=preset_id)
        with pytest.raises(PrometheusQueryPresetNotFound):
            await service.delete_preset(action)

    async def test_execute_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        mock_prometheus_client: MagicMock,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        prometheus_response = PrometheusQueryRangeResponse(
            status="success",
            data=PrometheusQueryData(result_type="matrix", result=[]),
        )
        mock_prometheus_client.query_range = AsyncMock(return_value=prometheus_response)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            options=ExecutePresetOptions(
                filter_labels={"kernel_id": "test-kernel"},
                group_labels=["kernel_id"],
            ),
            window="5m",
            time_range=time_range,
        )
        result = await service.execute_preset(action)

        assert result.response == prometheus_response
        mock_repository.get_by_id.assert_called_once_with(preset_data.id)
        mock_prometheus_client.query_range.assert_called_once()

    async def test_execute_preset_invalid_filter_label(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            options=ExecutePresetOptions(
                filter_labels={"invalid_label": "value"},
                group_labels=[],
            ),
            window="5m",
            time_range=time_range,
        )

        with pytest.raises(PrometheusQueryPresetInvalidLabel):
            await service.execute_preset(action)

    async def test_execute_preset_invalid_group_label(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            options=ExecutePresetOptions(
                filter_labels={},
                group_labels=["invalid_group"],
            ),
            window="5m",
            time_range=time_range,
        )

        with pytest.raises(PrometheusQueryPresetInvalidLabel):
            await service.execute_preset(action)

    async def test_execute_preset_window_fallback_to_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        mock_prometheus_client: MagicMock,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        """When request window is None, falls back to preset's time_window."""
        preset_data = replace(preset_data, time_window="10m")
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        prometheus_response = PrometheusQueryRangeResponse(
            status="success",
            data=PrometheusQueryData(result_type="matrix", result=[]),
        )
        mock_prometheus_client.query_range = AsyncMock(return_value=prometheus_response)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            options=ExecutePresetOptions(
                filter_labels={},
                group_labels=[],
            ),
            window=None,
            time_range=time_range,
        )
        result = await service.execute_preset(action)

        assert result.response == prometheus_response
        # Verify the preset was called (the window used is 10m from preset)
        call_args = mock_prometheus_client.query_range.call_args
        assert call_args.kwargs["preset"].window == "10m"

    async def test_execute_preset_window_fallback_to_server_default(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        mock_prometheus_client: MagicMock,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        """When both request and preset window are None, falls back to server config."""
        preset_data = replace(preset_data, time_window=None)
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        prometheus_response = PrometheusQueryRangeResponse(
            status="success",
            data=PrometheusQueryData(result_type="matrix", result=[]),
        )
        mock_prometheus_client.query_range = AsyncMock(return_value=prometheus_response)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            options=ExecutePresetOptions(
                filter_labels={},
                group_labels=[],
            ),
            window=None,
            time_range=time_range,
        )
        result = await service.execute_preset(action)

        assert result.response == prometheus_response
        # Verify the window used is the server default "1m"
        call_args = mock_prometheus_client.query_range.call_args
        assert call_args.kwargs["preset"].window == "1m"

    @pytest.fixture
    def time_range(self) -> QueryTimeRange:
        return QueryTimeRange(start="1704067200", end="1704153600", step="60s")

    async def test_execute_preset_empty_filter_labels_allows_any(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        mock_prometheus_client: MagicMock,
        preset_data: PrometheusQueryPresetData,
        time_range: QueryTimeRange,
    ) -> None:
        """When preset has empty filter_labels, any labels are allowed."""
        preset_data = replace(preset_data, filter_labels=[], group_labels=[])
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        prometheus_response = PrometheusQueryRangeResponse(
            status="success",
            data=PrometheusQueryData(result_type="matrix", result=[]),
        )
        mock_prometheus_client.query_range = AsyncMock(return_value=prometheus_response)

        action = ExecutePresetAction(
            preset_id=preset_data.id,
            options=ExecutePresetOptions(
                filter_labels={"any_label": "value"},
                group_labels=["any_group"],
            ),
            window="5m",
            time_range=time_range,
        )
        result = await service.execute_preset(action)

        assert result.response == prometheus_response
