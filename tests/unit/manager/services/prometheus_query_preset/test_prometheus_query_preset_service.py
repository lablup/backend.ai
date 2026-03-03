"""
Tests for PrometheusQueryPresetService functionality.
Tests the service layer with mocked repository and prometheus client.
"""

from __future__ import annotations

import uuid
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
from ai.backend.common.exception import InvalidAPIParameters, PrometheusQueryPresetNotFound
from ai.backend.manager.data.prometheus_query_preset import (
    PrometheusQueryPresetData,
    PrometheusQueryPresetListResult,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.prometheus_query_preset import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.prometheus_query_preset.actions.create_preset import (
    CreatePresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.delete_preset import (
    DeletePresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.execute_preset import (
    ExecutePresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.get_preset import (
    GetPresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.list_presets import (
    ListPresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.modify_preset import (
    ModifyPresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)


def _make_preset_data(
    *,
    preset_id: uuid.UUID | None = None,
    name: str = "cpu_usage",
    metric_name: str = "backendai_container_cpu_util",
    query_template: str = "rate(container_cpu_usage_seconds_total{{{labels}}}[{window}])",
    time_window: str | None = "5m",
    filter_labels: list[str] | None = None,
    group_labels: list[str] | None = None,
) -> PrometheusQueryPresetData:
    now = datetime.now(UTC)
    return PrometheusQueryPresetData(
        id=preset_id or uuid4(),
        name=name,
        metric_name=metric_name,
        query_template=query_template,
        time_window=time_window,
        filter_labels=["kernel_id", "session_id"] if filter_labels is None else filter_labels,
        group_labels=["kernel_id"] if group_labels is None else group_labels,
        created_at=now,
        updated_at=now,
    )


class TestPrometheusQueryPresetService:
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

    # =========================================================================
    # Tests - Create
    # =========================================================================

    async def test_create_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_data = _make_preset_data()
        mock_repository.create = AsyncMock(return_value=preset_data)

        creator = MagicMock(spec=Creator)
        action = CreatePresetAction(creator=creator)
        result = await service.create_preset(action)

        assert result.preset == preset_data
        mock_repository.create.assert_called_once_with(creator)

    # =========================================================================
    # Tests - Get
    # =========================================================================

    async def test_get_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_data = _make_preset_data()
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

    # =========================================================================
    # Tests - List
    # =========================================================================

    async def test_list_presets(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_data = _make_preset_data()
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
        action = ListPresetsAction(querier=querier)
        result = await service.list_presets(action)

        assert result.items == [preset_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search.assert_called_once_with(querier)

    async def test_list_presets_empty(
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
        action = ListPresetsAction(querier=querier)
        result = await service.list_presets(action)

        assert result.items == []
        assert result.total_count == 0

    # =========================================================================
    # Tests - Modify
    # =========================================================================

    async def test_modify_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_data = _make_preset_data()
        mock_repository.update = AsyncMock(return_value=preset_data)

        updater = MagicMock(spec=Updater)
        action = ModifyPresetAction(preset_id=preset_data.id, updater=updater)
        result = await service.modify_preset(action)

        assert result.preset == preset_data
        assert updater.pk_value == preset_data.id
        mock_repository.update.assert_called_once_with(updater)

    # =========================================================================
    # Tests - Delete
    # =========================================================================

    async def test_delete_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_id = uuid4()
        mock_repository.delete = AsyncMock(return_value=True)

        action = DeletePresetAction(preset_id=preset_id)
        result = await service.delete_preset(action)

        assert result.deleted is True
        mock_repository.delete.assert_called_once_with(preset_id)

    async def test_delete_preset_not_found(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_id = uuid4()
        mock_repository.delete = AsyncMock(return_value=False)

        action = DeletePresetAction(preset_id=preset_id)
        with pytest.raises(PrometheusQueryPresetNotFound):
            await service.delete_preset(action)

    # =========================================================================
    # Tests - Execute
    # =========================================================================

    async def test_execute_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        mock_prometheus_client: MagicMock,
    ) -> None:
        preset_data = _make_preset_data(
            filter_labels=["kernel_id", "session_id"],
            group_labels=["kernel_id"],
        )
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        prometheus_response = PrometheusQueryRangeResponse(
            status="success",
            data=PrometheusQueryData(result_type="matrix", result=[]),
        )
        mock_prometheus_client.query_range = AsyncMock(return_value=prometheus_response)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            labels={"kernel_id": "test-kernel"},
            group_labels=["kernel_id"],
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
    ) -> None:
        preset_data = _make_preset_data(
            filter_labels=["kernel_id", "session_id"],
        )
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            labels={"invalid_label": "value"},
            group_labels=[],
            window="5m",
            time_range=time_range,
        )

        with pytest.raises(InvalidAPIParameters, match="Invalid filter labels"):
            await service.execute_preset(action)

    async def test_execute_preset_invalid_group_label(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_data = _make_preset_data(
            group_labels=["kernel_id"],
        )
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            labels={},
            group_labels=["invalid_group"],
            window="5m",
            time_range=time_range,
        )

        with pytest.raises(InvalidAPIParameters, match="Invalid group labels"):
            await service.execute_preset(action)

    async def test_execute_preset_invalid_window_format(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
    ) -> None:
        preset_data = _make_preset_data()
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            labels={},
            group_labels=[],
            window="invalid",
            time_range=time_range,
        )

        with pytest.raises(InvalidAPIParameters, match="Invalid window format"):
            await service.execute_preset(action)

    async def test_execute_preset_window_fallback_to_preset(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        mock_prometheus_client: MagicMock,
    ) -> None:
        """When request window is None, falls back to preset's time_window."""
        preset_data = _make_preset_data(time_window="10m")
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        prometheus_response = PrometheusQueryRangeResponse(
            status="success",
            data=PrometheusQueryData(result_type="matrix", result=[]),
        )
        mock_prometheus_client.query_range = AsyncMock(return_value=prometheus_response)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            labels={},
            group_labels=[],
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
    ) -> None:
        """When both request and preset window are None, falls back to server config."""
        preset_data = _make_preset_data(time_window=None)
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        prometheus_response = PrometheusQueryRangeResponse(
            status="success",
            data=PrometheusQueryData(result_type="matrix", result=[]),
        )
        mock_prometheus_client.query_range = AsyncMock(return_value=prometheus_response)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            labels={},
            group_labels=[],
            window=None,
            time_range=time_range,
        )
        result = await service.execute_preset(action)

        assert result.response == prometheus_response
        # Verify the window used is the server default "1m"
        call_args = mock_prometheus_client.query_range.call_args
        assert call_args.kwargs["preset"].window == "1m"

    async def test_execute_preset_empty_filter_labels_allows_any(
        self,
        service: PrometheusQueryPresetService,
        mock_repository: MagicMock,
        mock_prometheus_client: MagicMock,
    ) -> None:
        """When preset has empty filter_labels, any labels are allowed."""
        preset_data = _make_preset_data(filter_labels=[], group_labels=[])
        mock_repository.get_by_id = AsyncMock(return_value=preset_data)

        prometheus_response = PrometheusQueryRangeResponse(
            status="success",
            data=PrometheusQueryData(result_type="matrix", result=[]),
        )
        mock_prometheus_client.query_range = AsyncMock(return_value=prometheus_response)

        time_range = QueryTimeRange(start="1704067200", end="1704153600", step="60s")
        action = ExecutePresetAction(
            preset_id=preset_data.id,
            labels={"any_label": "value"},
            group_labels=["any_group"],
            window="5m",
            time_range=time_range,
        )
        result = await service.execute_preset(action)

        assert result.response == prometheus_response
