"""
Tests for AuditLogRepository functionality.
Tests the repository layer with real database operations.
"""

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
from ai.backend.manager.repositories.base import BatchQuerier, Creator, OffsetPagination
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestAuditLogRepository:
    """Test cases for AuditLogRepository"""

    # =========================================================================
    # Fixtures
    # =========================================================================

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(database_connection, [AuditLogRow]):
            yield database_connection

    @pytest.fixture
    def audit_log_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AuditLogRepository:
        """Create an AuditLogRepository instance"""
        return AuditLogRepository(db=db_with_cleanup)

    @pytest.fixture
    async def sample_audit_logs_for_filtering(
        self,
        audit_log_repository: AuditLogRepository,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Create sample audit logs with different entity_types for filter testing"""
        now = datetime.now(UTC)
        entity_map: dict[str, uuid.UUID] = {}

        test_data = [
            ("session", "create", OperationStatus.SUCCESS),
            ("agent", "start", OperationStatus.SUCCESS),
        ]

        for entity_type, operation, status in test_data:
            creator = Creator(
                spec=AuditLogCreatorSpec(
                    action_id=uuid.uuid4(),
                    entity_type=entity_type,
                    operation=operation,
                    created_at=now,
                    description=f"{entity_type} {operation}",
                    status=status,
                    entity_id=None,
                    request_id=None,
                    triggered_by=None,
                    duration=None,
                )
            )
            result = await audit_log_repository.create(creator)
            entity_map[entity_type] = result.id

        yield entity_map

    @pytest.fixture
    async def sample_audit_logs_for_ordering(
        self,
        audit_log_repository: AuditLogRepository,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create sample audit logs with predictable operations for ordering tests"""
        now = datetime.now(UTC)
        audit_log_ids: list[uuid.UUID] = []
        operations = ["alpha-op", "beta-op", "gamma-op", "delta-op"]

        for operation in operations:
            creator = Creator(
                spec=AuditLogCreatorSpec(
                    action_id=uuid.uuid4(),
                    entity_type="session",
                    operation=operation,
                    created_at=now,
                    description=f"Operation {operation}",
                    status=OperationStatus.SUCCESS,
                    entity_id=None,
                    request_id=None,
                    triggered_by=None,
                    duration=None,
                )
            )
            result = await audit_log_repository.create(creator)
            audit_log_ids.append(result.id)

        yield audit_log_ids

    @pytest.fixture
    async def sample_audit_logs_for_pagination(
        self,
        audit_log_repository: AuditLogRepository,
    ) -> AsyncGenerator[list[uuid.UUID], None]:
        """Create 25 audit logs for pagination testing"""
        now = datetime.now(UTC)
        audit_log_ids: list[uuid.UUID] = []

        for i in range(25):
            creator = Creator(
                spec=AuditLogCreatorSpec(
                    action_id=uuid.uuid4(),
                    entity_type="session",
                    operation=f"operation_{i:02d}",
                    created_at=now,
                    description=f"Operation {i}",
                    status=OperationStatus.SUCCESS,
                    entity_id=None,
                    request_id=None,
                    triggered_by=None,
                    duration=None,
                )
            )
            result = await audit_log_repository.create(creator)
            audit_log_ids.append(result.id)

        yield audit_log_ids

    # =========================================================================
    # Tests - Create
    # =========================================================================

    async def test_create_multiple_audit_logs(
        self,
        audit_log_repository: AuditLogRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test creating multiple audit logs"""
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
            create_result = await audit_log_repository.create(creator)
            assert create_result.status == status

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            count_result = await db_sess.execute(
                sa.select(sa.func.count()).select_from(AuditLogRow)
            )
            count = count_result.scalar()
            assert count == 3

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    async def test_search_audit_logs_filter_by_entity_type(
        self,
        audit_log_repository: AuditLogRepository,
        sample_audit_logs_for_filtering: dict[str, uuid.UUID],
    ) -> None:
        """Test searching audit logs filtered by entity_type returns only matching audit logs"""
        target_entity_type = "session"

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: AuditLogRow.entity_type == target_entity_type,
            ],
            orders=[],
        )

        result = await audit_log_repository.search(querier=querier)

        result_ids = [log.id for log in result.items]
        assert sample_audit_logs_for_filtering["session"] in result_ids
        assert sample_audit_logs_for_filtering["agent"] not in result_ids

    async def test_search_audit_logs_filter_by_operation_pattern(
        self,
        audit_log_repository: AuditLogRepository,
        sample_audit_logs_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching audit logs with operation pattern filter"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: AuditLogRow.operation.like("alpha%"),
            ],
            orders=[],
        )

        result = await audit_log_repository.search(querier=querier)

        assert len(result.items) == 1
        assert result.items[0].operation == "alpha-op"

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    async def test_search_audit_logs_order_by_operation_ascending(
        self,
        audit_log_repository: AuditLogRepository,
        sample_audit_logs_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching audit logs ordered by operation ascending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[AuditLogRow.operation.asc()],
        )

        result = await audit_log_repository.search(querier=querier)

        result_operations = [log.operation for log in result.items]
        assert result_operations == sorted(result_operations)
        assert result_operations[0] == "alpha-op"
        assert result_operations[-1] == "gamma-op"

    async def test_search_audit_logs_order_by_operation_descending(
        self,
        audit_log_repository: AuditLogRepository,
        sample_audit_logs_for_ordering: list[uuid.UUID],
    ) -> None:
        """Test searching audit logs ordered by operation descending"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[AuditLogRow.operation.desc()],
        )

        result = await audit_log_repository.search(querier=querier)

        result_operations = [log.operation for log in result.items]
        assert result_operations == sorted(result_operations, reverse=True)
        assert result_operations[0] == "gamma-op"
        assert result_operations[-1] == "alpha-op"

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    async def test_search_audit_logs_offset_pagination_first_page(
        self,
        audit_log_repository: AuditLogRepository,
        sample_audit_logs_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await audit_log_repository.search(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_audit_logs_offset_pagination_second_page(
        self,
        audit_log_repository: AuditLogRepository,
        sample_audit_logs_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await audit_log_repository.search(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 25

    async def test_search_audit_logs_offset_pagination_last_page(
        self,
        audit_log_repository: AuditLogRepository,
        sample_audit_logs_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=20),
            conditions=[],
            orders=[],
        )

        result = await audit_log_repository.search(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 25

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    async def test_search_audit_logs_with_pagination_filter_and_order(
        self,
        audit_log_repository: AuditLogRepository,
        sample_audit_logs_for_pagination: list[uuid.UUID],
    ) -> None:
        """Test searching audit logs with pagination, filter condition, and ordering combined"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=5, offset=2),
            conditions=[
                # TODO: Refactor after adding Condition type
                lambda: AuditLogRow.entity_type == "session",
            ],
            orders=[AuditLogRow.operation.asc()],
        )

        result = await audit_log_repository.search(querier=querier)

        assert result.total_count == 25
        assert len(result.items) == 5

        result_operations = [log.operation for log in result.items]
        assert result_operations == sorted(result_operations)
