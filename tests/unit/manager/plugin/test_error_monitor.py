"""Tests for ErrorMonitor plugin."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.logging import LogLevel
from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.plugin.error_monitor import ErrorMonitor
from ai.backend.manager.repositories.error_log.creators import ErrorLogCreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.models.error_logs import ErrorLogRow
    from ai.backend.manager.repositories.base import Creator


class TestErrorMonitor:
    """Test cases for ErrorMonitor plugin."""

    @pytest.fixture
    def mock_error_log_repository(self) -> AsyncMock:
        """Create a mock ErrorLogRepository."""
        return AsyncMock()

    @pytest.fixture
    def mock_root_context(self, mock_error_log_repository: AsyncMock) -> dict[str, Any]:
        """Create a mock root context with repositories."""
        root_ctx = MagicMock()
        root_ctx.repositories.error_log.repository = mock_error_log_repository
        return {"_root.context": root_ctx}

    @pytest.fixture
    async def error_monitor(self, mock_root_context: dict[str, Any]) -> ErrorMonitor:
        """Create an initialized ErrorMonitor instance."""
        monitor = ErrorMonitor(plugin_config={}, local_config={})
        await monitor.init(context=mock_root_context)
        return monitor

    async def test_capture_exception_creates_error_log(
        self,
        error_monitor: ErrorMonitor,
        mock_error_log_repository: AsyncMock,
    ) -> None:
        """Test that capture_exception creates an error log entry with correct data."""

        test_user_id = uuid.uuid4()
        test_exception = ValueError("Test error message")

        await error_monitor.capture_exception(
            exc_instance=test_exception,
            context={"severity": LogLevel.ERROR, "user": test_user_id},
        )

        mock_error_log_repository.create.assert_called_once()
        call_args = mock_error_log_repository.create.call_args
        creator: Creator[ErrorLogRow] = call_args[0][0]
        spec = creator.spec
        assert isinstance(spec, ErrorLogCreatorSpec)

        assert spec.severity == ErrorLogSeverity.ERROR
        assert spec.source == "manager"
        assert spec.user == test_user_id
        assert "ValueError: Test error message" in spec.message
        assert spec.context_lang == "python"
