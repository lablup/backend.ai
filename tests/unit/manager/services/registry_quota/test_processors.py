"""
Unit tests for RegistryQuotaProcessors.

Tests verify that processors correctly delegate to service methods
and that ActionMonitor lifecycle is properly managed.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.services.registry_quota.actions.create_registry_quota import (
    CreateRegistryQuotaAction,
    CreateRegistryQuotaActionResult,
)
from ai.backend.manager.services.registry_quota.actions.delete_registry_quota import (
    DeleteRegistryQuotaAction,
    DeleteRegistryQuotaActionResult,
)
from ai.backend.manager.services.registry_quota.actions.read_registry_quota import (
    ReadRegistryQuotaAction,
    ReadRegistryQuotaActionResult,
)
from ai.backend.manager.services.registry_quota.actions.update_registry_quota import (
    UpdateRegistryQuotaAction,
    UpdateRegistryQuotaActionResult,
)
from ai.backend.manager.services.registry_quota.processors import RegistryQuotaProcessors
from ai.backend.manager.services.registry_quota.service import RegistryQuotaService


class TestCreateRegistryQuotaProcessor:
    @pytest.fixture
    def mock_service(self) -> MagicMock:
        mock = MagicMock(spec=RegistryQuotaService)
        project_id = uuid.uuid4()
        mock.create_registry_quota = AsyncMock(
            return_value=CreateRegistryQuotaActionResult(project_id=project_id)
        )
        mock._project_id = project_id
        return mock

    @pytest.fixture
    def mock_monitor(self) -> MagicMock:
        mock = MagicMock(spec=ActionMonitor)
        mock.prepare = AsyncMock()
        mock.done = AsyncMock()
        return mock

    @pytest.fixture
    def processors(
        self, mock_service: MagicMock, mock_monitor: MagicMock
    ) -> RegistryQuotaProcessors:
        return RegistryQuotaProcessors(mock_service, [mock_monitor])

    @pytest.mark.asyncio
    async def test_create_registry_quota_processor_calls_service(
        self,
        processors: RegistryQuotaProcessors,
        mock_service: MagicMock,
    ) -> None:
        # Given
        project_id = mock_service._project_id
        action = CreateRegistryQuotaAction(project_id=project_id, quota=1024)

        # When
        result = await processors.create_registry_quota.wait_for_complete(action)

        # Then
        assert isinstance(result, CreateRegistryQuotaActionResult)
        assert result.project_id == project_id
        mock_service.create_registry_quota.assert_called_once_with(action)

    @pytest.mark.asyncio
    async def test_create_registry_quota_processor_calls_monitor(
        self,
        processors: RegistryQuotaProcessors,
        mock_service: MagicMock,
        mock_monitor: MagicMock,
    ) -> None:
        # Given
        project_id = mock_service._project_id
        action = CreateRegistryQuotaAction(project_id=project_id, quota=1024)

        # When
        await processors.create_registry_quota.wait_for_complete(action)

        # Then
        mock_monitor.prepare.assert_called_once()
        mock_monitor.done.assert_called_once()


class TestReadRegistryQuotaProcessor:
    @pytest.fixture
    def mock_service(self) -> MagicMock:
        mock = MagicMock(spec=RegistryQuotaService)
        project_id = uuid.uuid4()
        mock.read_registry_quota = AsyncMock(
            return_value=ReadRegistryQuotaActionResult(project_id=project_id, quota=2048)
        )
        mock._project_id = project_id
        return mock

    @pytest.fixture
    def mock_monitor(self) -> MagicMock:
        mock = MagicMock(spec=ActionMonitor)
        mock.prepare = AsyncMock()
        mock.done = AsyncMock()
        return mock

    @pytest.fixture
    def processors(
        self, mock_service: MagicMock, mock_monitor: MagicMock
    ) -> RegistryQuotaProcessors:
        return RegistryQuotaProcessors(mock_service, [mock_monitor])

    @pytest.mark.asyncio
    async def test_read_registry_quota_processor_calls_service(
        self,
        processors: RegistryQuotaProcessors,
        mock_service: MagicMock,
    ) -> None:
        # Given
        project_id = mock_service._project_id
        action = ReadRegistryQuotaAction(project_id=project_id)

        # When
        result = await processors.read_registry_quota.wait_for_complete(action)

        # Then
        assert isinstance(result, ReadRegistryQuotaActionResult)
        assert result.project_id == project_id
        assert result.quota == 2048
        mock_service.read_registry_quota.assert_called_once_with(action)


class TestUpdateRegistryQuotaProcessor:
    @pytest.fixture
    def mock_service(self) -> MagicMock:
        mock = MagicMock(spec=RegistryQuotaService)
        project_id = uuid.uuid4()
        mock.update_registry_quota = AsyncMock(
            return_value=UpdateRegistryQuotaActionResult(project_id=project_id)
        )
        mock._project_id = project_id
        return mock

    @pytest.fixture
    def mock_monitor(self) -> MagicMock:
        mock = MagicMock(spec=ActionMonitor)
        mock.prepare = AsyncMock()
        mock.done = AsyncMock()
        return mock

    @pytest.fixture
    def processors(
        self, mock_service: MagicMock, mock_monitor: MagicMock
    ) -> RegistryQuotaProcessors:
        return RegistryQuotaProcessors(mock_service, [mock_monitor])

    @pytest.mark.asyncio
    async def test_update_registry_quota_processor_calls_service(
        self,
        processors: RegistryQuotaProcessors,
        mock_service: MagicMock,
    ) -> None:
        # Given
        project_id = mock_service._project_id
        action = UpdateRegistryQuotaAction(project_id=project_id, quota=4096)

        # When
        result = await processors.update_registry_quota.wait_for_complete(action)

        # Then
        assert isinstance(result, UpdateRegistryQuotaActionResult)
        assert result.project_id == project_id
        mock_service.update_registry_quota.assert_called_once_with(action)


class TestDeleteRegistryQuotaProcessor:
    @pytest.fixture
    def mock_service(self) -> MagicMock:
        mock = MagicMock(spec=RegistryQuotaService)
        project_id = uuid.uuid4()
        mock.delete_registry_quota = AsyncMock(
            return_value=DeleteRegistryQuotaActionResult(project_id=project_id)
        )
        mock._project_id = project_id
        return mock

    @pytest.fixture
    def mock_monitor(self) -> MagicMock:
        mock = MagicMock(spec=ActionMonitor)
        mock.prepare = AsyncMock()
        mock.done = AsyncMock()
        return mock

    @pytest.fixture
    def processors(
        self, mock_service: MagicMock, mock_monitor: MagicMock
    ) -> RegistryQuotaProcessors:
        return RegistryQuotaProcessors(mock_service, [mock_monitor])

    @pytest.mark.asyncio
    async def test_delete_registry_quota_processor_calls_service(
        self,
        processors: RegistryQuotaProcessors,
        mock_service: MagicMock,
    ) -> None:
        # Given
        project_id = mock_service._project_id
        action = DeleteRegistryQuotaAction(project_id=project_id)

        # When
        result = await processors.delete_registry_quota.wait_for_complete(action)

        # Then
        assert isinstance(result, DeleteRegistryQuotaActionResult)
        assert result.project_id == project_id
        mock_service.delete_registry_quota.assert_called_once_with(action)
