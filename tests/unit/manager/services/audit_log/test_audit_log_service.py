from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.repositories.audit_log import AuditLogRepository
from ai.backend.manager.repositories.audit_log.creators import AuditLogCreatorSpec
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.services.audit_log.actions.create import CreateAuditLogAction
from ai.backend.manager.services.audit_log.service import AuditLogService


class TestAuditLogService:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AuditLogRepository)

    @pytest.fixture
    def audit_log_service(self, mock_repository: MagicMock) -> AuditLogService:
        return AuditLogService(audit_log_repository=mock_repository)

    @pytest.fixture
    def sample_audit_log_data(self) -> AuditLogData:
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

    async def test_create_audit_log(
        self,
        audit_log_service: AuditLogService,
        mock_repository: MagicMock,
        sample_audit_log_data: AuditLogData,
    ) -> None:
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
