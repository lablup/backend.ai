from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.audit_log import AuditLogCreatorSpec, AuditLogRepository
from ai.backend.manager.repositories.base import Creator
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestAuditLogRepository:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [AuditLogRow]):
            yield database_connection

    @pytest.fixture
    def audit_log_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AuditLogRepository:
        return AuditLogRepository(db=db_with_cleanup)

    async def test_create_multiple_audit_logs(
        self,
        audit_log_repository: AuditLogRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        now = datetime.now(UTC)
        statuses = [OperationStatus.SUCCESS, OperationStatus.ERROR, OperationStatus.RUNNING]

        for i, status in enumerate(statuses):
            data = AuditLogData(
                id=uuid.uuid4(),
                action_id=uuid.uuid4(),
                entity_type="agent",
                operation=f"operation_{i}",
                created_at=now,
                description=f"Operation {i}",
                status=status,
                entity_id=None,
                request_id=None,
                triggered_by=None,
                duration=None,
            )
            creator = Creator(
                spec=AuditLogCreatorSpec(
                    action_id=data.action_id,
                    entity_type=data.entity_type,
                    operation=data.operation,
                    created_at=data.created_at,
                    description=data.description,
                    status=data.status,
                    entity_id=data.entity_id,
                    request_id=data.request_id,
                    triggered_by=data.triggered_by,
                    duration=data.duration,
                )
            )
            result = await audit_log_repository.create(creator)
            assert result.status == status

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await db_sess.execute(sa.select(sa.func.count()).select_from(AuditLogRow))
            count = result.scalar()
            assert count == 3
