"""
Tests for AuditLogRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.audit_log import AuditLogCreatorSpec, AuditLogRepository
from ai.backend.manager.repositories.base import Creator
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestAuditLogRepository:
    """Test cases for AuditLogRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                AuditLogRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def audit_log_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AuditLogRepository:
        """Create AuditLogRepository instance with database"""
        return AuditLogRepository(db=db_with_cleanup)

    async def test_create_audit_log(
        self,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        """Test creating an audit log entry"""
        action_id = uuid.uuid4()
        now = datetime.now(UTC)

        creator = Creator(
            spec=AuditLogCreatorSpec(
                action_id=action_id,
                entity_type="session",
                operation="create",
                created_at=now,
                description="Session created successfully",
                status=OperationStatus.SUCCESS,
                entity_id="session-123",
                request_id="req-456",
                triggered_by="user-789",
                duration=timedelta(seconds=1, milliseconds=500),
            )
        )

        row = await audit_log_repository.create(creator)

        assert row is not None
        assert row.action_id == action_id
        assert row.entity_type == "session"
        assert row.operation == "create"
        assert row.description == "Session created successfully"
        assert row.status == OperationStatus.SUCCESS
        assert row.entity_id == "session-123"
        assert row.request_id == "req-456"
        assert row.triggered_by == "user-789"
        assert row.duration == timedelta(seconds=1, milliseconds=500)
        assert row.id is not None

    async def test_create_audit_log_with_minimal_fields(
        self,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        """Test creating an audit log entry with only required fields"""
        action_id = uuid.uuid4()
        now = datetime.now(UTC)

        creator = Creator(
            spec=AuditLogCreatorSpec(
                action_id=action_id,
                entity_type="image",
                operation="delete",
                created_at=now,
                description="Image deleted",
                status=OperationStatus.ERROR,
            )
        )

        row = await audit_log_repository.create(creator)

        assert row is not None
        assert row.action_id == action_id
        assert row.entity_type == "image"
        assert row.operation == "delete"
        assert row.description == "Image deleted"
        assert row.status == OperationStatus.ERROR
        assert row.entity_id is None
        assert row.request_id is None
        assert row.triggered_by is None
        assert row.duration is None

    async def test_create_multiple_audit_logs(
        self,
        audit_log_repository: AuditLogRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test creating multiple audit log entries"""
        now = datetime.now(UTC)
        statuses = [OperationStatus.SUCCESS, OperationStatus.ERROR, OperationStatus.RUNNING]

        for i, status in enumerate(statuses):
            creator = Creator(
                spec=AuditLogCreatorSpec(
                    action_id=uuid.uuid4(),
                    entity_type="agent",
                    operation=f"operation_{i}",
                    created_at=now,
                    description=f"Operation {i}",
                    status=status,
                )
            )
            row = await audit_log_repository.create(creator)
            assert row.status == status

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await db_sess.execute(sa.select(sa.func.count()).select_from(AuditLogRow))
            count = result.scalar()
            assert count == 3

    async def test_create_audit_log_persists_to_database(
        self,
        audit_log_repository: AuditLogRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that created audit log is persisted to database"""
        action_id = uuid.uuid4()
        now = datetime.now(UTC)

        creator = Creator(
            spec=AuditLogCreatorSpec(
                action_id=action_id,
                entity_type="vfolder",
                operation="update",
                created_at=now,
                description="VFolder updated",
                status=OperationStatus.SUCCESS,
                entity_id="vfolder-abc",
            )
        )

        created_row = await audit_log_repository.create(creator)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(AuditLogRow).where(AuditLogRow.id == created_row.id)
            )
            db_row = result.scalar_one()

            assert db_row.action_id == action_id
            assert db_row.entity_type == "vfolder"
            assert db_row.operation == "update"
            assert db_row.entity_id == "vfolder-abc"

    async def test_create_audit_log_with_all_entity_types(
        self,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        """Test creating audit logs with various entity types"""
        now = datetime.now(UTC)
        entity_types = [
            "image",
            "container_registry",
            "domain",
            "group",
            "agent",
            "session",
            "user",
            "vfolder",
        ]

        for entity_type in entity_types:
            creator = Creator(
                spec=AuditLogCreatorSpec(
                    action_id=uuid.uuid4(),
                    entity_type=entity_type,
                    operation="test",
                    created_at=now,
                    description=f"Test {entity_type}",
                    status=OperationStatus.SUCCESS,
                )
            )
            row = await audit_log_repository.create(creator)
            assert row.entity_type == entity_type

    async def test_create_audit_log_with_different_operations(
        self,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        """Test creating audit logs with different operation types"""
        now = datetime.now(UTC)
        operations = ["create", "read", "update", "delete", "start", "stop", "restart"]

        for operation in operations:
            creator = Creator(
                spec=AuditLogCreatorSpec(
                    action_id=uuid.uuid4(),
                    entity_type="session",
                    operation=operation,
                    created_at=now,
                    description=f"Session {operation}",
                    status=OperationStatus.SUCCESS,
                )
            )
            row = await audit_log_repository.create(creator)
            assert row.operation == operation
