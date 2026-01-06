"""
Tests for ErrorLogService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.error_log.types import ErrorLogData, ErrorLogSeverity
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.error_log import ErrorLogCreatorSpec, ErrorLogRepository
from ai.backend.manager.services.error_log.actions import CreateErrorLogAction
from ai.backend.manager.services.error_log.service import ErrorLogService


class TestErrorLogService:
    """Test cases for ErrorLogService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked ErrorLogRepository"""
        return MagicMock(spec=ErrorLogRepository)

    @pytest.fixture
    def error_log_service(self, mock_repository: MagicMock) -> ErrorLogService:
        """Create ErrorLogService instance with mocked repository"""
        return ErrorLogService(repository=mock_repository)

    @pytest.fixture
    def sample_error_log_data(self) -> ErrorLogData:
        """Create sample error log data"""
        return ErrorLogData(
            id=uuid.uuid4(),
            created_at=datetime.now(tz=UTC),
            severity=ErrorLogSeverity.ERROR,
            source="manager",
            user=uuid.uuid4(),
            is_read=False,
            is_cleared=False,
            message="Test error message",
            context_lang="en",
            context_env={"test": "value"},
            request_url="/api/v1/test",
            request_status=500,
            traceback="Traceback: ...",
        )

    @pytest.mark.asyncio
    async def test_create_error_log(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
        sample_error_log_data: ErrorLogData,
    ) -> None:
        """Test creating an error log through service"""
        mock_repository.create = AsyncMock(return_value=sample_error_log_data)

        creator = Creator(spec=ErrorLogCreatorSpec(sample_error_log_data))
        action = CreateErrorLogAction(creator=creator)

        result = await error_log_service.create(action)

        assert result.error_log_data == sample_error_log_data
        mock_repository.create.assert_called_once_with(creator)

    @pytest.mark.asyncio
    async def test_create_multiple_error_logs(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
    ) -> None:
        """Test creating multiple error logs through service"""
        now = datetime.now(tz=UTC)
        user_id = uuid.uuid4()

        error_logs = [
            ErrorLogData(
                id=uuid.uuid4(),
                created_at=now,
                severity=ErrorLogSeverity.CRITICAL,
                source="manager",
                user=user_id,
                is_read=False,
                is_cleared=False,
                message="Critical error",
                context_lang="en",
                context_env={},
                request_url=None,
                request_status=None,
                traceback=None,
            ),
            ErrorLogData(
                id=uuid.uuid4(),
                created_at=now,
                severity=ErrorLogSeverity.WARNING,
                source="agent",
                user=None,
                is_read=False,
                is_cleared=False,
                message="Warning message",
                context_lang="ko",
                context_env={"key": "value"},
                request_url="/api/v1/test",
                request_status=400,
                traceback=None,
            ),
        ]

        results = []
        for error_log in error_logs:
            mock_repository.create = AsyncMock(return_value=error_log)
            creator = Creator(spec=ErrorLogCreatorSpec(error_log))
            action = CreateErrorLogAction(creator=creator)
            result = await error_log_service.create(action)
            results.append(result)

        assert len(results) == 2
        assert results[0].error_log_data.severity == ErrorLogSeverity.CRITICAL
        assert results[0].error_log_data.source == "manager"
        assert results[1].error_log_data.severity == ErrorLogSeverity.WARNING
        assert results[1].error_log_data.source == "agent"

    @pytest.mark.asyncio
    async def test_create_error_log_without_user(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
    ) -> None:
        """Test creating an error log without user (system error)"""
        error_log_data = ErrorLogData(
            id=uuid.uuid4(),
            created_at=datetime.now(tz=UTC),
            severity=ErrorLogSeverity.ERROR,
            source="system",
            user=None,
            is_read=False,
            is_cleared=False,
            message="System error",
            context_lang="en",
            context_env={"component": "scheduler"},
            request_url=None,
            request_status=None,
            traceback="System traceback...",
        )

        mock_repository.create = AsyncMock(return_value=error_log_data)

        creator = Creator(spec=ErrorLogCreatorSpec(error_log_data))
        action = CreateErrorLogAction(creator=creator)

        result = await error_log_service.create(action)

        assert result.error_log_data.user is None
        assert result.error_log_data.source == "system"
        assert result.error_log_data.message == "System error"
