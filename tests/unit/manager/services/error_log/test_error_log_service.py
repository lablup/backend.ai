"""
Tests for ErrorLogService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.identifier.error_log import ErrorLogID
from ai.backend.manager.data.error_log.types import (
    ErrorLogContent,
    ErrorLogData,
    ErrorLogMeta,
    ErrorLogSeverity,
)
from ai.backend.manager.errors.resource import DBOperationFailed
from ai.backend.manager.repositories.error_log import ErrorLogRepository
from ai.backend.manager.services.error_log.actions.mark_cleared import MarkClearedErrorLogAction
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
            id=ErrorLogID(uuid.uuid4()),
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

    async def test_superadmin_marks_error_log_cleared(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
    ) -> None:
        """Superadmin marks error log as cleared successfully."""
        log_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        mock_repository.mark_cleared = AsyncMock(return_value=1)

        action = MarkClearedErrorLogAction(
            log_id=log_id,
            user_uuid=user_uuid,
            user_domain="default",
            is_superadmin=True,
            is_admin=True,
        )

        result = await error_log_service.mark_cleared(action)

        assert result is not None
        mock_repository.mark_cleared.assert_called_once_with(
            log_id=log_id,
            user_uuid=user_uuid,
            user_domain="default",
            is_superadmin=True,
            is_admin=True,
        )

    async def test_nonexistent_log_raises_db_operation_failed(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
    ) -> None:
        """Non-existent log_id raises DBOperationFailed (rowcount != 1)."""
        mock_repository.mark_cleared = AsyncMock(return_value=0)

        action = MarkClearedErrorLogAction(
            log_id=uuid.uuid4(),
            user_uuid=uuid.uuid4(),
            user_domain="default",
            is_superadmin=True,
            is_admin=True,
        )

        with pytest.raises(DBOperationFailed):
            await error_log_service.mark_cleared(action)

    async def test_already_cleared_log_is_idempotent(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
    ) -> None:
        """Already cleared log returns success if rowcount is 1."""
        mock_repository.mark_cleared = AsyncMock(return_value=1)

        action = MarkClearedErrorLogAction(
            log_id=uuid.uuid4(),
            user_uuid=uuid.uuid4(),
            user_domain="default",
            is_superadmin=True,
            is_admin=True,
        )

        result = await error_log_service.mark_cleared(action)

        assert result is not None

    async def test_non_admin_user_mark_cleared(
        self,
        error_log_service: ErrorLogService,
        mock_repository: MagicMock,
    ) -> None:
        """Non-admin user can mark cleared if repository permits (cross-domain check)."""
        log_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        mock_repository.mark_cleared = AsyncMock(return_value=1)

        action = MarkClearedErrorLogAction(
            log_id=log_id,
            user_uuid=user_uuid,
            user_domain="other-domain",
            is_superadmin=False,
            is_admin=False,
        )

        result = await error_log_service.mark_cleared(action)

        assert result is not None
        mock_repository.mark_cleared.assert_called_once_with(
            log_id=log_id,
            user_uuid=user_uuid,
            user_domain="other-domain",
            is_superadmin=False,
            is_admin=False,
        )
