"""
Tests for SchedulingHistoryRepository functionality.
Tests the repository layer with real database operations.

Note: This repository is read-only. History records are created via
SchedulerDBSource.update_with_history() during actual scheduling operations.
These tests verify the search functionality with directly inserted test data.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.deployment.types import RouteStatus
from ai.backend.manager.data.kernel.types import KernelSchedulingPhase
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionStatus,
)
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.scheduling_history import (
    SchedulingHistoryRepository,
)
from ai.backend.manager.repositories.scheduling_history.options import (
    DeploymentHistoryConditions,
    KernelSchedulingHistoryConditions,
    RouteHistoryConditions,
    SessionSchedulingHistoryConditions,
)
from ai.backend.testutils.db import with_tables


class TestSchedulingHistoryRepository:
    """Test cases for SchedulingHistoryRepository (read-only)"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                SessionSchedulingHistoryRow,
                KernelSchedulingHistoryRow,
                DeploymentHistoryRow,
                RouteHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scheduling_history_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[SchedulingHistoryRepository, None]:
        """Create SchedulingHistoryRepository instance with database"""
        repo = SchedulingHistoryRepository(db=db_with_cleanup)
        yield repo

    # ========== Session History Tests ==========

    @pytest.mark.asyncio
    async def test_search_session_history_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history with pagination"""
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search with pagination
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[SessionSchedulingHistoryConditions.by_session_id(session_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_session_history(querier)

        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is False

    @pytest.mark.asyncio
    async def test_search_session_history_by_session_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history filtered by session_id"""
        session_id_1 = SessionId(uuid.uuid4())
        session_id_2 = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            # Create history for session 1
            for i in range(3):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id_1,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Session 1 - Message {i}",
                    attempts=1,
                )
                db_sess.add(row)

            # Create history for session 2
            for i in range(2):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id_2,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Session 2 - Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search for session 1 only
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[SessionSchedulingHistoryConditions.by_session_id(session_id_1)],
            orders=[],
        )
        result = await scheduling_history_repository.search_session_history(querier)

        assert result.total_count == 3
        assert all(item.session_id == session_id_1 for item in result.items)

    @pytest.mark.asyncio
    async def test_search_session_history_by_result(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history filtered by result"""
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            # Success records
            for i in range(3):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Success {i}",
                    attempts=1,
                )
                db_sess.add(row)

            # Failure records
            for i in range(2):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id,
                    phase=f"FAIL_PHASE_{i}",
                    result=str(SchedulingResult.FAILURE),
                    error_code="TEST_ERROR",
                    message=f"Failure {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search for failures only
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                SessionSchedulingHistoryConditions.by_session_id(session_id),
                SessionSchedulingHistoryConditions.by_results([SchedulingResult.FAILURE]),
            ],
            orders=[],
        )
        result = await scheduling_history_repository.search_session_history(querier)

        assert result.total_count == 2
        assert all(item.result == SchedulingResult.FAILURE for item in result.items)

    @pytest.mark.asyncio
    async def test_search_session_history_with_status_transition(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history with from/to status"""
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            row = SessionSchedulingHistoryRow(
                session_id=session_id,
                phase="SCHEDULE",
                from_status=str(SessionStatus.PENDING),
                to_status=str(SessionStatus.SCHEDULED),
                result=str(SchedulingResult.SUCCESS),
                message="Scheduled successfully",
                attempts=1,
            )
            db_sess.add(row)
            await db_sess.flush()

        # Search
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[SessionSchedulingHistoryConditions.by_session_id(session_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_session_history(querier)

        assert result.total_count == 1
        item = result.items[0]
        assert item.from_status == SessionStatus.PENDING
        assert item.to_status == SessionStatus.SCHEDULED

    # ========== Kernel History Tests ==========

    @pytest.mark.asyncio
    async def test_search_kernel_history_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching kernel history with pagination"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                row = KernelSchedulingHistoryRow(
                    kernel_id=kernel_id,
                    session_id=session_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search with pagination
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[KernelSchedulingHistoryConditions.by_kernel_id(kernel_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_kernel_history(querier)

        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is False

    @pytest.mark.asyncio
    async def test_search_kernel_history_with_status_transition(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching kernel history with from/to status"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            row = KernelSchedulingHistoryRow(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PREPARING",
                from_status=str(KernelSchedulingPhase.PREPARING),
                to_status=str(KernelSchedulingPhase.PREPARED),
                result=str(SchedulingResult.SUCCESS),
                message="Kernel prepared",
                attempts=1,
            )
            db_sess.add(row)
            await db_sess.flush()

        # Search
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[KernelSchedulingHistoryConditions.by_kernel_id(kernel_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_kernel_history(querier)

        assert result.total_count == 1
        item = result.items[0]
        assert item.from_status == KernelSchedulingPhase.PREPARING
        assert item.to_status == KernelSchedulingPhase.PREPARED

    # ========== Deployment History Tests ==========

    @pytest.mark.asyncio
    async def test_search_deployment_history_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching deployment history with pagination"""
        deployment_id = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                row = DeploymentHistoryRow(
                    deployment_id=deployment_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search with pagination
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[DeploymentHistoryConditions.by_deployment_id(deployment_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_deployment_history(querier)

        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is False

    @pytest.mark.asyncio
    async def test_search_deployment_history_by_result(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching deployment history filtered by result"""
        deployment_id = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            # Success records
            for i in range(2):
                row = DeploymentHistoryRow(
                    deployment_id=deployment_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Success {i}",
                    attempts=1,
                )
                db_sess.add(row)

            # Failure records
            for i in range(3):
                row = DeploymentHistoryRow(
                    deployment_id=deployment_id,
                    phase=f"FAIL_PHASE_{i}",
                    result=str(SchedulingResult.FAILURE),
                    error_code="RESOURCE_LIMIT",
                    message=f"Failure {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search for failures only
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                DeploymentHistoryConditions.by_deployment_id(deployment_id),
                DeploymentHistoryConditions.by_results([SchedulingResult.FAILURE]),
            ],
            orders=[],
        )
        result = await scheduling_history_repository.search_deployment_history(querier)

        assert result.total_count == 3
        assert all(item.result == SchedulingResult.FAILURE for item in result.items)

    # ========== Route History Tests ==========

    @pytest.mark.asyncio
    async def test_search_route_history_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching route history with pagination"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                row = RouteHistoryRow(
                    route_id=route_id,
                    deployment_id=deployment_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search with pagination
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[RouteHistoryConditions.by_route_id(route_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_route_history(querier)

        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is False

    @pytest.mark.asyncio
    async def test_search_route_history_with_status_transition(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching route history with from/to status"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            row = RouteHistoryRow(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="PROVISION",
                from_status=str(RouteStatus.PROVISIONING.value),
                to_status=str(RouteStatus.HEALTHY.value),
                result=str(SchedulingResult.SUCCESS),
                message="Route provisioned",
                attempts=1,
            )
            db_sess.add(row)
            await db_sess.flush()

        # Search
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[RouteHistoryConditions.by_route_id(route_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_route_history(querier)

        assert result.total_count == 1
        item = result.items[0]
        assert item.from_status == RouteStatus.PROVISIONING
        assert item.to_status == RouteStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_search_route_history_by_deployment_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching route history filtered by deployment_id"""
        deployment_id_1 = uuid.uuid4()
        deployment_id_2 = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            # Create history for deployment 1
            for i in range(3):
                row = RouteHistoryRow(
                    route_id=uuid.uuid4(),
                    deployment_id=deployment_id_1,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Deployment 1 - Message {i}",
                    attempts=1,
                )
                db_sess.add(row)

            # Create history for deployment 2
            for i in range(2):
                row = RouteHistoryRow(
                    route_id=uuid.uuid4(),
                    deployment_id=deployment_id_2,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Deployment 2 - Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search for deployment 1 only
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[RouteHistoryConditions.by_deployment_id(deployment_id_1)],
            orders=[],
        )
        result = await scheduling_history_repository.search_route_history(querier)

        assert result.total_count == 3
        assert all(item.deployment_id == deployment_id_1 for item in result.items)
