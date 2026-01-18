"""Tests for GroupConfigProcessors functionality."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.errors.storage import DotfileNotFound
from ai.backend.manager.models.group import GroupDotfile
from ai.backend.manager.services.group_config.actions.create_dotfile import (
    CreateDotfileAction,
    CreateDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.delete_dotfile import (
    DeleteDotfileAction,
    DeleteDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.get_dotfile import (
    GetDotfileAction,
    GetDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.list_dotfiles import (
    ListDotfilesAction,
    ListDotfilesActionResult,
)
from ai.backend.manager.services.group_config.actions.update_dotfile import (
    UpdateDotfileAction,
    UpdateDotfileActionResult,
)
from ai.backend.manager.services.group_config.processors import GroupConfigProcessors
from ai.backend.manager.services.group_config.service import GroupConfigService


@pytest.fixture
def group_id() -> uuid.UUID:
    return uuid.uuid4()


class TestGroupConfigProcessorsInit:
    def test_processors_has_all_action_processors(self) -> None:
        mock_service = MagicMock(spec=GroupConfigService)
        processors = GroupConfigProcessors(mock_service, [])

        assert hasattr(processors, "create_dotfile")
        assert hasattr(processors, "list_dotfiles")
        assert hasattr(processors, "get_dotfile")
        assert hasattr(processors, "update_dotfile")
        assert hasattr(processors, "delete_dotfile")

    def test_supported_actions(self) -> None:
        mock_service = MagicMock(spec=GroupConfigService)
        processors = GroupConfigProcessors(mock_service, [])
        supported = processors.supported_actions()
        operation_types = {spec.operation_type for spec in supported}

        assert "create_dotfile" in operation_types
        assert "list_dotfiles" in operation_types
        assert "get_dotfile" in operation_types
        assert "update_dotfile" in operation_types
        assert "delete_dotfile" in operation_types


class TestCreateDotfileProcessor:
    @pytest.mark.asyncio
    async def test_create_dotfile_processor_calls_service(self, group_id: uuid.UUID) -> None:
        expected_result = CreateDotfileActionResult(group_id=group_id)
        mock_service = MagicMock(spec=GroupConfigService)
        mock_service.create_dotfile = AsyncMock(return_value=expected_result)
        processors = GroupConfigProcessors(mock_service, [])

        action = CreateDotfileAction(
            group_id=group_id,
            path=".bashrc",
            data="# test",
            permission="644",
        )
        result = await processors.create_dotfile.wait_for_complete(action)

        assert result.group_id == group_id
        mock_service.create_dotfile.assert_called_once_with(action)


class TestListDotfilesProcessor:
    @pytest.mark.asyncio
    async def test_list_dotfiles_processor_calls_service(self, group_id: uuid.UUID) -> None:
        expected_dotfiles: list[GroupDotfile] = [
            {"path": ".bashrc", "perm": "644", "data": "# test"}
        ]
        expected_result = ListDotfilesActionResult(dotfiles=expected_dotfiles)
        mock_service = MagicMock(spec=GroupConfigService)
        mock_service.list_dotfiles = AsyncMock(return_value=expected_result)
        processors = GroupConfigProcessors(mock_service, [])

        action = ListDotfilesAction(group_id=group_id)
        result = await processors.list_dotfiles.wait_for_complete(action)

        assert result.dotfiles == expected_dotfiles
        mock_service.list_dotfiles.assert_called_once_with(action)


class TestGetDotfileProcessor:
    @pytest.mark.asyncio
    async def test_get_dotfile_processor_calls_service(self, group_id: uuid.UUID) -> None:
        expected_dotfile: GroupDotfile = {"path": ".bashrc", "perm": "644", "data": "# test"}
        expected_result = GetDotfileActionResult(dotfile=expected_dotfile)
        mock_service = MagicMock(spec=GroupConfigService)
        mock_service.get_dotfile = AsyncMock(return_value=expected_result)
        processors = GroupConfigProcessors(mock_service, [])

        action = GetDotfileAction(group_id=group_id, path=".bashrc")
        result = await processors.get_dotfile.wait_for_complete(action)

        assert result.dotfile == expected_dotfile
        mock_service.get_dotfile.assert_called_once_with(action)

    @pytest.mark.asyncio
    async def test_get_dotfile_processor_propagates_error(self, group_id: uuid.UUID) -> None:
        mock_service = MagicMock(spec=GroupConfigService)
        mock_service.get_dotfile = AsyncMock(side_effect=DotfileNotFound)
        processors = GroupConfigProcessors(mock_service, [])

        action = GetDotfileAction(group_id=group_id, path=".nonexistent")

        with pytest.raises(DotfileNotFound):
            await processors.get_dotfile.wait_for_complete(action)


class TestUpdateDotfileProcessor:
    @pytest.mark.asyncio
    async def test_update_dotfile_processor_calls_service(self, group_id: uuid.UUID) -> None:
        expected_result = UpdateDotfileActionResult(group_id=group_id)
        mock_service = MagicMock(spec=GroupConfigService)
        mock_service.update_dotfile = AsyncMock(return_value=expected_result)
        processors = GroupConfigProcessors(mock_service, [])

        action = UpdateDotfileAction(
            group_id=group_id,
            path=".bashrc",
            data="# updated",
            permission="755",
        )
        result = await processors.update_dotfile.wait_for_complete(action)

        assert result.group_id == group_id
        mock_service.update_dotfile.assert_called_once_with(action)


class TestDeleteDotfileProcessor:
    @pytest.mark.asyncio
    async def test_delete_dotfile_processor_calls_service(self, group_id: uuid.UUID) -> None:
        expected_result = DeleteDotfileActionResult(success=True)
        mock_service = MagicMock(spec=GroupConfigService)
        mock_service.delete_dotfile = AsyncMock(return_value=expected_result)
        processors = GroupConfigProcessors(mock_service, [])

        action = DeleteDotfileAction(group_id=group_id, path=".bashrc")
        result = await processors.delete_dotfile.wait_for_complete(action)

        assert result.success is True
        mock_service.delete_dotfile.assert_called_once_with(action)


class TestProcessorWithMonitors:
    @pytest.mark.asyncio
    async def test_monitors_are_called(self, group_id: uuid.UUID) -> None:
        mock_monitor = MagicMock(spec=ActionMonitor)
        mock_monitor.prepare = AsyncMock()
        mock_monitor.done = AsyncMock()

        expected_result = ListDotfilesActionResult(dotfiles=[])
        mock_service = MagicMock(spec=GroupConfigService)
        mock_service.list_dotfiles = AsyncMock(return_value=expected_result)
        processors = GroupConfigProcessors(mock_service, [mock_monitor])

        action = ListDotfilesAction(group_id=group_id)
        await processors.list_dotfiles.wait_for_complete(action)

        mock_monitor.prepare.assert_called_once()
        mock_monitor.done.assert_called_once()
