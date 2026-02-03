"""
Tests for AuditLogService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogListResult
from ai.backend.manager.repositories.audit_log import AuditLogRepository
from ai.backend.manager.repositories.audit_log.creators import AuditLogCreatorSpec
from ai.backend.manager.repositories.base import BatchQuerier, Creator, OffsetPagination
from ai.backend.manager.services.audit_log.actions.create import CreateAuditLogAction
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction
from ai.backend.manager.services.audit_log.service import AuditLogService


class TestAuditLogService:
    """Test cases for AuditLogService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked AuditLogRepository"""
        return MagicMock(spec=AuditLogRepository)

    @pytest.fixture
    def audit_log_service(self, mock_repository: MagicMock) -> AuditLogService:
        """Create AuditLogService instance with mocked repository"""
        return AuditLogService(audit_log_repository=mock_repository)

    @pytest.fixture
    def sample_audit_log_data(self) -> AuditLogData:
        """Create sample audit log data"""
        return AuditLogData(
            id=uuid.uuid4(),
            action_id=uuid.uuid4(),
            entity_type="session",
            operation="create",
            created_at=datetime.now(UTC),
            description="Session created",
            status=OperationStatus.SUCCESS,
            entity_id="session-123",
            request_id="req-456",
            triggered_by="user-789",
            duration=timedelta(seconds=1),
        )

    # =========================================================================
    # Tests - Create
    # =========================================================================

    async def test_create_audit_log(
        self,
        audit_log_service: AuditLogService,
        mock_repository: MagicMock,
        sample_audit_log_data: AuditLogData,
    ) -> None:
        """Test creating an audit log"""
        mock_repository.create = AsyncMock(return_value=sample_audit_log_data)

        creator = Creator(
            spec=AuditLogCreatorSpec(
                action_id=sample_audit_log_data.action_id,
                entity_type=sample_audit_log_data.entity_type,
                operation=sample_audit_log_data.operation,
                created_at=sample_audit_log_data.created_at,
                description=sample_audit_log_data.description,
                status=sample_audit_log_data.status,
                entity_id=sample_audit_log_data.entity_id,
                request_id=sample_audit_log_data.request_id,
                triggered_by=sample_audit_log_data.triggered_by,
                duration=sample_audit_log_data.duration,
            )
        )
        action = CreateAuditLogAction(creator=creator)
        result = await audit_log_service.create(action)

        assert result.audit_log_id == sample_audit_log_data.id
        mock_repository.create.assert_called_once_with(creator)

    # =========================================================================
    # Tests - Search
    # =========================================================================

    async def test_search_audit_logs(
        self,
        audit_log_service: AuditLogService,
        mock_repository: MagicMock,
        sample_audit_log_data: AuditLogData,
    ) -> None:
        """Test searching audit logs with querier"""
        mock_repository.search = AsyncMock(
            return_value=AuditLogListResult(
                items=[sample_audit_log_data],
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
        action = SearchAuditLogsAction(querier=querier)
        result = await audit_log_service.search(action)

        assert result.data == [sample_audit_log_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search.assert_called_once_with(querier)

    async def test_search_audit_logs_empty_result(
        self,
        audit_log_service: AuditLogService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching audit logs when no results are found"""
        mock_repository.search = AsyncMock(
            return_value=AuditLogListResult(
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
        action = SearchAuditLogsAction(querier=querier)
        result = await audit_log_service.search(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_audit_logs_with_pagination(
        self,
        audit_log_service: AuditLogService,
        mock_repository: MagicMock,
        sample_audit_log_data: AuditLogData,
    ) -> None:
        """Test searching audit logs with pagination"""
        mock_repository.search = AsyncMock(
            return_value=AuditLogListResult(
                items=[sample_audit_log_data],
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
        action = SearchAuditLogsAction(querier=querier)
        result = await audit_log_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
