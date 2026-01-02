"""
Tests for SchedulingHistoryRepository functionality.
Tests the repository layer with real database operations.
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
    SubStepResult,
)
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, Creator, OffsetPagination
from ai.backend.manager.repositories.scheduling_history import (
    DeploymentHistoryCreatorSpec,
    KernelSchedulingHistoryCreatorSpec,
    RouteHistoryCreatorSpec,
    SchedulingHistoryRepository,
    SessionSchedulingHistoryCreatorSpec,
)
from ai.backend.manager.repositories.scheduling_history.options import (
    DeploymentHistoryConditions,
    KernelSchedulingHistoryConditions,
    RouteHistoryConditions,
    SessionSchedulingHistoryConditions,
)
from ai.backend.testutils.db import with_tables


class TestSchedulingHistoryRepository:
    """Test cases for SchedulingHistoryRepository"""

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
    async def test_record_session_history_success(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test recording session history with SUCCESS result"""
        session_id = SessionId(uuid.uuid4())

        creator = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.SUCCESS,
                message="Session scheduled successfully",
                from_status=SessionStatus.PENDING,
                to_status=SessionStatus.SCHEDULED,
            )
        )

        result = await scheduling_history_repository.record_session_history(creator)

        assert result.session_id == session_id
        assert result.phase == "SCHEDULE"
        assert result.result == SchedulingResult.SUCCESS
        assert result.from_status == SessionStatus.PENDING
        assert result.to_status == SessionStatus.SCHEDULED
        assert result.attempts == 1
        assert result.error_code is None

    @pytest.mark.asyncio
    async def test_record_session_history_failure(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test recording session history with FAILURE result"""
        session_id = SessionId(uuid.uuid4())

        creator = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.FAILURE,
                message="No available resources",
                error_code="RESOURCE_EXHAUSTED",
            )
        )

        result = await scheduling_history_repository.record_session_history(creator)

        assert result.session_id == session_id
        assert result.result == SchedulingResult.FAILURE
        assert result.error_code == "RESOURCE_EXHAUSTED"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_record_session_history_merge_on_failure(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that repeated failures with same phase+error_code merge (attempts++)"""
        session_id = SessionId(uuid.uuid4())

        # First failure
        creator1 = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_EXHAUSTED",
                message="No resources available",
            )
        )
        result1 = await scheduling_history_repository.record_session_history(creator1)
        assert result1.attempts == 1

        # Second failure with same phase+error_code -> should merge
        creator2 = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_EXHAUSTED",
                message="Still no resources",
            )
        )
        result2 = await scheduling_history_repository.record_session_history(creator2)

        assert result2.id == result1.id  # Same row
        assert result2.attempts == 2  # Incremented

        # Third failure -> should merge again
        creator3 = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_EXHAUSTED",
                message="Resources still unavailable",
            )
        )
        result3 = await scheduling_history_repository.record_session_history(creator3)

        assert result3.id == result1.id
        assert result3.attempts == 3

    @pytest.mark.asyncio
    async def test_record_session_history_no_merge_on_success(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that SUCCESS results never merge"""
        session_id = SessionId(uuid.uuid4())

        # First success
        creator1 = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.SUCCESS,
                error_code=None,
                message="Scheduled",
            )
        )
        result1 = await scheduling_history_repository.record_session_history(creator1)

        # Second success -> should NOT merge (new row)
        creator2 = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.SUCCESS,
                error_code=None,
                message="Scheduled again",
            )
        )
        result2 = await scheduling_history_repository.record_session_history(creator2)

        assert result2.id != result1.id  # Different row
        assert result2.attempts == 1

    @pytest.mark.asyncio
    async def test_record_session_history_no_merge_different_phase(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that failures with different phase do not merge"""
        session_id = SessionId(uuid.uuid4())

        # First failure
        creator1 = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_EXHAUSTED",
                message="No resources",
            )
        )
        result1 = await scheduling_history_repository.record_session_history(creator1)

        # Second failure with different phase -> should NOT merge
        creator2 = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="PREPARE",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_EXHAUSTED",
                message="Prepare failed",
            )
        )
        result2 = await scheduling_history_repository.record_session_history(creator2)

        assert result2.id != result1.id  # Different row

    @pytest.mark.asyncio
    async def test_record_session_history_no_merge_different_error_code(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that failures with different error_code do not merge"""
        session_id = SessionId(uuid.uuid4())

        # First failure
        creator1 = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_EXHAUSTED",
                message="No resources",
            )
        )
        result1 = await scheduling_history_repository.record_session_history(creator1)

        # Second failure with different error_code -> should NOT merge
        creator2 = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.FAILURE,
                error_code="QUOTA_EXCEEDED",
                message="Quota exceeded",
            )
        )
        result2 = await scheduling_history_repository.record_session_history(creator2)

        assert result2.id != result1.id  # Different row

    @pytest.mark.asyncio
    async def test_record_session_history_with_sub_steps(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test recording session history with sub_steps"""
        session_id = SessionId(uuid.uuid4())

        sub_steps = [
            SubStepResult(
                step="validate_resources",
                result=SchedulingResult.SUCCESS,
                message="Resources validated",
            ),
            SubStepResult(
                step="allocate_agent",
                result=SchedulingResult.FAILURE,
                error_code="NO_AGENT",
                message="No agent available",
            ),
        ]

        creator = Creator(
            spec=SessionSchedulingHistoryCreatorSpec(
                session_id=session_id,
                phase="SCHEDULE",
                result=SchedulingResult.FAILURE,
                error_code="NO_AGENT",
                message="Scheduling failed",
                sub_steps=sub_steps,
            )
        )

        result = await scheduling_history_repository.record_session_history(creator)

        assert result.sub_steps is not None
        assert len(result.sub_steps) == 2
        assert result.sub_steps[0].step == "validate_resources"
        assert result.sub_steps[0].result == SchedulingResult.SUCCESS
        assert result.sub_steps[1].step == "allocate_agent"
        assert result.sub_steps[1].error_code == "NO_AGENT"

    @pytest.mark.asyncio
    async def test_search_session_history_pagination(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history with pagination"""
        session_id = SessionId(uuid.uuid4())

        # Create multiple history entries
        for i in range(5):
            creator = Creator(
                spec=SessionSchedulingHistoryCreatorSpec(
                    session_id=session_id,
                    phase=f"PHASE_{i}",
                    result=SchedulingResult.SUCCESS,
                    message=f"Message {i}",
                )
            )
            await scheduling_history_repository.record_session_history(creator)

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
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history filtered by session_id"""
        session_id_1 = SessionId(uuid.uuid4())
        session_id_2 = SessionId(uuid.uuid4())

        # Create history for session 1
        for i in range(3):
            creator = Creator(
                spec=SessionSchedulingHistoryCreatorSpec(
                    session_id=session_id_1,
                    phase=f"PHASE_{i}",
                    result=SchedulingResult.SUCCESS,
                    message=f"Session 1 - Message {i}",
                )
            )
            await scheduling_history_repository.record_session_history(creator)

        # Create history for session 2
        for i in range(2):
            creator = Creator(
                spec=SessionSchedulingHistoryCreatorSpec(
                    session_id=session_id_2,
                    phase=f"PHASE_{i}",
                    result=SchedulingResult.SUCCESS,
                    message=f"Session 2 - Message {i}",
                )
            )
            await scheduling_history_repository.record_session_history(creator)

        # Search for session 1 only
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[SessionSchedulingHistoryConditions.by_session_id(session_id_1)],
            orders=[],
        )
        result = await scheduling_history_repository.search_session_history(querier)

        assert result.total_count == 3
        assert all(item.session_id == session_id_1 for item in result.items)

    # ========== Kernel History Tests ==========

    @pytest.mark.asyncio
    async def test_record_kernel_history_success(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test recording kernel history with SUCCESS result"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        creator = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PREPARING",
                result=SchedulingResult.SUCCESS,
                message="Kernel prepared",
                from_status=KernelSchedulingPhase.PREPARING,
                to_status=KernelSchedulingPhase.PREPARED,
            )
        )

        result = await scheduling_history_repository.record_kernel_history(creator)

        assert result.kernel_id == kernel_id
        assert result.session_id == session_id
        assert result.result == SchedulingResult.SUCCESS
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_record_kernel_history_failure(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test recording kernel history with FAILURE result"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        creator = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PULLING",
                result=SchedulingResult.FAILURE,
                message="Image pull failed",
                error_code="IMAGE_NOT_FOUND",
            )
        )

        result = await scheduling_history_repository.record_kernel_history(creator)

        assert result.kernel_id == kernel_id
        assert result.result == SchedulingResult.FAILURE
        assert result.error_code == "IMAGE_NOT_FOUND"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_record_kernel_history_merge_on_failure(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that repeated kernel failures merge"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        # First failure
        creator1 = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PULLING",
                result=SchedulingResult.FAILURE,
                error_code="IMAGE_NOT_FOUND",
                message="Image not found",
            )
        )
        result1 = await scheduling_history_repository.record_kernel_history(creator1)
        assert result1.attempts == 1

        # Second failure with same phase+error_code -> should merge
        creator2 = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PULLING",
                result=SchedulingResult.FAILURE,
                error_code="IMAGE_NOT_FOUND",
                message="Still cannot find image",
            )
        )
        result2 = await scheduling_history_repository.record_kernel_history(creator2)

        assert result2.id == result1.id
        assert result2.attempts == 2

        # Third failure -> should merge again
        creator3 = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PULLING",
                result=SchedulingResult.FAILURE,
                error_code="IMAGE_NOT_FOUND",
                message="Image still unavailable",
            )
        )
        result3 = await scheduling_history_repository.record_kernel_history(creator3)

        assert result3.id == result1.id
        assert result3.attempts == 3

    @pytest.mark.asyncio
    async def test_record_kernel_history_no_merge_on_success(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that SUCCESS results never merge"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        # First success
        creator1 = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PULLING",
                result=SchedulingResult.SUCCESS,
                message="Image pulled",
            )
        )
        result1 = await scheduling_history_repository.record_kernel_history(creator1)

        # Second success -> should NOT merge (new row)
        creator2 = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PULLING",
                result=SchedulingResult.SUCCESS,
                message="Image pulled again",
            )
        )
        result2 = await scheduling_history_repository.record_kernel_history(creator2)

        assert result2.id != result1.id
        assert result2.attempts == 1

    @pytest.mark.asyncio
    async def test_record_kernel_history_no_merge_different_phase(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that failures with different phase do not merge"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        # First failure
        creator1 = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PULLING",
                result=SchedulingResult.FAILURE,
                error_code="IMAGE_NOT_FOUND",
                message="Image not found",
            )
        )
        result1 = await scheduling_history_repository.record_kernel_history(creator1)

        # Second failure with different phase -> should NOT merge
        creator2 = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PREPARING",
                result=SchedulingResult.FAILURE,
                error_code="IMAGE_NOT_FOUND",
                message="Prepare failed",
            )
        )
        result2 = await scheduling_history_repository.record_kernel_history(creator2)

        assert result2.id != result1.id

    @pytest.mark.asyncio
    async def test_record_kernel_history_no_merge_different_error_code(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that failures with different error_code do not merge"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        # First failure
        creator1 = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PULLING",
                result=SchedulingResult.FAILURE,
                error_code="IMAGE_NOT_FOUND",
                message="Image not found",
            )
        )
        result1 = await scheduling_history_repository.record_kernel_history(creator1)

        # Second failure with different error_code -> should NOT merge
        creator2 = Creator(
            spec=KernelSchedulingHistoryCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PULLING",
                result=SchedulingResult.FAILURE,
                error_code="REGISTRY_UNAVAILABLE",
                message="Registry down",
            )
        )
        result2 = await scheduling_history_repository.record_kernel_history(creator2)

        assert result2.id != result1.id

    @pytest.mark.asyncio
    async def test_search_kernel_history_pagination(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching kernel history with pagination"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        # Create multiple history entries
        for i in range(5):
            creator = Creator(
                spec=KernelSchedulingHistoryCreatorSpec(
                    kernel_id=kernel_id,
                    session_id=session_id,
                    phase=f"PHASE_{i}",
                    result=SchedulingResult.SUCCESS,
                    message=f"Message {i}",
                )
            )
            await scheduling_history_repository.record_kernel_history(creator)

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

    # ========== Deployment History Tests ==========

    @pytest.mark.asyncio
    async def test_record_deployment_history_success(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test recording deployment history with SUCCESS result"""
        deployment_id = uuid.uuid4()

        creator = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.SUCCESS,
                message="Deployment provisioned",
            )
        )

        result = await scheduling_history_repository.record_deployment_history(creator)

        assert result.deployment_id == deployment_id
        assert result.result == SchedulingResult.SUCCESS
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_record_deployment_history_failure(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test recording deployment history with FAILURE result"""
        deployment_id = uuid.uuid4()

        creator = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.FAILURE,
                message="Deployment provision failed",
                error_code="RESOURCE_LIMIT",
            )
        )

        result = await scheduling_history_repository.record_deployment_history(creator)

        assert result.deployment_id == deployment_id
        assert result.result == SchedulingResult.FAILURE
        assert result.error_code == "RESOURCE_LIMIT"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_record_deployment_history_merge_on_failure(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that repeated deployment failures merge"""
        deployment_id = uuid.uuid4()

        # First failure
        creator1 = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_LIMIT",
                message="Resource limit reached",
            )
        )
        result1 = await scheduling_history_repository.record_deployment_history(creator1)

        # Second failure -> should merge
        creator2 = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_LIMIT",
                message="Still at resource limit",
            )
        )
        result2 = await scheduling_history_repository.record_deployment_history(creator2)

        assert result2.id == result1.id
        assert result2.attempts == 2

        # Third failure -> should merge again
        creator3 = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_LIMIT",
                message="Resource limit still exceeded",
            )
        )
        result3 = await scheduling_history_repository.record_deployment_history(creator3)

        assert result3.id == result1.id
        assert result3.attempts == 3

    @pytest.mark.asyncio
    async def test_record_deployment_history_no_merge_on_success(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that SUCCESS results never merge"""
        deployment_id = uuid.uuid4()

        # First success
        creator1 = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.SUCCESS,
                message="Deployment provisioned",
            )
        )
        result1 = await scheduling_history_repository.record_deployment_history(creator1)

        # Second success -> should NOT merge (new row)
        creator2 = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.SUCCESS,
                message="Deployment provisioned again",
            )
        )
        result2 = await scheduling_history_repository.record_deployment_history(creator2)

        assert result2.id != result1.id
        assert result2.attempts == 1

    @pytest.mark.asyncio
    async def test_record_deployment_history_no_merge_different_phase(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that failures with different phase do not merge"""
        deployment_id = uuid.uuid4()

        # First failure
        creator1 = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_LIMIT",
                message="Resource limit reached",
            )
        )
        result1 = await scheduling_history_repository.record_deployment_history(creator1)

        # Second failure with different phase -> should NOT merge
        creator2 = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="SCALE_UP",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_LIMIT",
                message="Scale up failed",
            )
        )
        result2 = await scheduling_history_repository.record_deployment_history(creator2)

        assert result2.id != result1.id

    @pytest.mark.asyncio
    async def test_record_deployment_history_no_merge_different_error_code(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that failures with different error_code do not merge"""
        deployment_id = uuid.uuid4()

        # First failure
        creator1 = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.FAILURE,
                error_code="RESOURCE_LIMIT",
                message="Resource limit reached",
            )
        )
        result1 = await scheduling_history_repository.record_deployment_history(creator1)

        # Second failure with different error_code -> should NOT merge
        creator2 = Creator(
            spec=DeploymentHistoryCreatorSpec(
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.FAILURE,
                error_code="NO_AVAILABLE_AGENT",
                message="No agent available",
            )
        )
        result2 = await scheduling_history_repository.record_deployment_history(creator2)

        assert result2.id != result1.id

    @pytest.mark.asyncio
    async def test_search_deployment_history_pagination(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching deployment history with pagination"""
        deployment_id = uuid.uuid4()

        # Create multiple history entries
        for i in range(5):
            creator = Creator(
                spec=DeploymentHistoryCreatorSpec(
                    deployment_id=deployment_id,
                    phase=f"PHASE_{i}",
                    result=SchedulingResult.SUCCESS,
                    message=f"Message {i}",
                )
            )
            await scheduling_history_repository.record_deployment_history(creator)

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

    # ========== Route History Tests ==========

    @pytest.mark.asyncio
    async def test_record_route_history_success(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test recording route history with SUCCESS result"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        creator = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.SUCCESS,
                message="Route provisioned",
                from_status=RouteStatus.PROVISIONING,
                to_status=RouteStatus.HEALTHY,
            )
        )

        result = await scheduling_history_repository.record_route_history(creator)

        assert result.route_id == route_id
        assert result.deployment_id == deployment_id
        assert result.result == SchedulingResult.SUCCESS
        assert result.from_status == RouteStatus.PROVISIONING
        assert result.to_status == RouteStatus.HEALTHY
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_record_route_history_failure(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test recording route history with FAILURE result"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        creator = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="HEALTH_CHECK",
                result=SchedulingResult.FAILURE,
                message="Health check failed",
                error_code="HEALTH_CHECK_FAILED",
            )
        )

        result = await scheduling_history_repository.record_route_history(creator)

        assert result.route_id == route_id
        assert result.deployment_id == deployment_id
        assert result.result == SchedulingResult.FAILURE
        assert result.error_code == "HEALTH_CHECK_FAILED"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_record_route_history_merge_on_failure(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that repeated route failures merge"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        # First failure
        creator1 = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="HEALTH_CHECK",
                result=SchedulingResult.FAILURE,
                error_code="HEALTH_CHECK_FAILED",
                message="Health check failed",
            )
        )
        result1 = await scheduling_history_repository.record_route_history(creator1)

        # Second failure -> should merge
        creator2 = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="HEALTH_CHECK",
                result=SchedulingResult.FAILURE,
                error_code="HEALTH_CHECK_FAILED",
                message="Health check still failing",
            )
        )
        result2 = await scheduling_history_repository.record_route_history(creator2)

        assert result2.id == result1.id
        assert result2.attempts == 2

        # Third failure -> should merge again
        creator3 = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="HEALTH_CHECK",
                result=SchedulingResult.FAILURE,
                error_code="HEALTH_CHECK_FAILED",
                message="Health check continuously failing",
            )
        )
        result3 = await scheduling_history_repository.record_route_history(creator3)

        assert result3.id == result1.id
        assert result3.attempts == 3

    @pytest.mark.asyncio
    async def test_record_route_history_no_merge_on_success(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that SUCCESS results never merge"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        # First success
        creator1 = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="HEALTH_CHECK",
                result=SchedulingResult.SUCCESS,
                message="Health check passed",
            )
        )
        result1 = await scheduling_history_repository.record_route_history(creator1)

        # Second success -> should NOT merge (new row)
        creator2 = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="HEALTH_CHECK",
                result=SchedulingResult.SUCCESS,
                message="Health check passed again",
            )
        )
        result2 = await scheduling_history_repository.record_route_history(creator2)

        assert result2.id != result1.id
        assert result2.attempts == 1

    @pytest.mark.asyncio
    async def test_record_route_history_no_merge_different_phase(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that failures with different phase do not merge"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        # First failure
        creator1 = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="HEALTH_CHECK",
                result=SchedulingResult.FAILURE,
                error_code="HEALTH_CHECK_FAILED",
                message="Health check failed",
            )
        )
        result1 = await scheduling_history_repository.record_route_history(creator1)

        # Second failure with different phase -> should NOT merge
        creator2 = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="PROVISION",
                result=SchedulingResult.FAILURE,
                error_code="HEALTH_CHECK_FAILED",
                message="Provision failed",
            )
        )
        result2 = await scheduling_history_repository.record_route_history(creator2)

        assert result2.id != result1.id

    @pytest.mark.asyncio
    async def test_record_route_history_no_merge_different_error_code(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that failures with different error_code do not merge"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        # First failure
        creator1 = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="HEALTH_CHECK",
                result=SchedulingResult.FAILURE,
                error_code="HEALTH_CHECK_FAILED",
                message="Health check failed",
            )
        )
        result1 = await scheduling_history_repository.record_route_history(creator1)

        # Second failure with different error_code -> should NOT merge
        creator2 = Creator(
            spec=RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="HEALTH_CHECK",
                result=SchedulingResult.FAILURE,
                error_code="TIMEOUT",
                message="Request timed out",
            )
        )
        result2 = await scheduling_history_repository.record_route_history(creator2)

        assert result2.id != result1.id

    @pytest.mark.asyncio
    async def test_search_route_history_pagination(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching route history with pagination"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        # Create multiple history entries
        for i in range(5):
            creator = Creator(
                spec=RouteHistoryCreatorSpec(
                    route_id=route_id,
                    deployment_id=deployment_id,
                    phase=f"PHASE_{i}",
                    result=SchedulingResult.SUCCESS,
                    message=f"Message {i}",
                )
            )
            await scheduling_history_repository.record_route_history(creator)

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
