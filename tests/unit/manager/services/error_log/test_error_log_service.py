"""
Tests for ErrorLogService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.error_log.types import (
    ErrorLogContent,
    ErrorLogData,
    ErrorLogListResult,
    ErrorLogMeta,
    ErrorLogSeverity,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator, OffsetPagination
from ai.backend.manager.repositories.error_log import ErrorLogCreatorSpec, ErrorLogRepository
from ai.backend.manager.services.error_log.actions import CreateErrorLogAction
from ai.backend.manager.services.error_log.actions.search import SearchErrorLogsAction
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
            meta=ErrorLogMeta(
                created_at=datetime.now(tz=UTC),
                user=uuid.uuid4(),
                source="manager",
                is_read=False,
                is_cleared=False,
                context_lang="en",
                context_env={"test": "value"},
                request_url="/api/v1/test",
                request_status=500,
            ),
            content=ErrorLogContent(
                severity=ErrorLogSeverity.ERROR,
                message="Test error message",
                traceback="Traceback: ...",
            ),
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

        creator = Creator(
            spec=ErrorLogCreatorSpec(
                severity=sample_error_log_data.content.severity,
                source=sample_error_log_data.meta.source,
                message=sample_error_log_data.content.message,
                context_lang=sample_error_log_data.meta.context_lang,
                context_env=sample_error_log_data.meta.context_env,
                user=sample_error_log_data.meta.user,
                is_read=sample_error_log_data.meta.is_read,
                is_cleared=sample_error_log_data.meta.is_cleared,
                request_url=sample_error_log_data.meta.request_url,
                request_status=sample_error_log_data.meta.request_status,
                traceback=sample_error_log_data.content.traceback,
            )
        )
        action = CreateErrorLogAction(creator=creator)

        result = await error_log_service.create(action)

        assert result.error_log_data == sample_error_log_data
        mock_repository.create.assert_called_once_with(creator)

    # =========================================================================
    # Tests - Search
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_error_logs(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
        sample_error_log_data: ErrorLogData,
    ) -> None:
        """Test searching error logs with querier"""
        mock_repository.search = AsyncMock(
            return_value=ErrorLogListResult(
                items=[sample_error_log_data],
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
        action = SearchErrorLogsAction(querier=querier)
        result = await error_log_service.search(action)

        assert result.data == [sample_error_log_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search.assert_called_once_with(querier)

    @pytest.mark.asyncio
    async def test_search_error_logs_empty_result(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching error logs when no results are found"""
        mock_repository.search = AsyncMock(
            return_value=ErrorLogListResult(
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
        action = SearchErrorLogsAction(querier=querier)
        result = await error_log_service.search(action)

        assert result.data == []
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_search_error_logs_with_pagination(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
        sample_error_log_data: ErrorLogData,
    ) -> None:
        """Test searching error logs with pagination"""
        mock_repository.search = AsyncMock(
            return_value=ErrorLogListResult(
                items=[sample_error_log_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchErrorLogsAction(querier=querier)
        result = await error_log_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
