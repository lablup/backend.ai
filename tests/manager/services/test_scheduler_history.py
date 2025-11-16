from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import SessionId
from ai.backend.manager.models.scheduler_history import (
    SchedulerExecutionHistoryRow,
    SchedulerExecutionStatus,
    SchedulerExecutionStep,
)
from ai.backend.manager.repositories.scheduler_history import SchedulerHistoryRepository
from ai.backend.manager.services.scheduler_history import SchedulerHistoryService


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    return AsyncMock(spec=SASession)


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create a mock repository."""
    return AsyncMock(spec=SchedulerHistoryRepository)


@pytest.fixture
def service(mock_db_session: AsyncMock) -> SchedulerHistoryService:
    """Create a service instance with mock session."""
    return SchedulerHistoryService(mock_db_session)


@pytest.fixture
def sample_session_id() -> SessionId:
    """Create a sample session ID."""
    return SessionId(uuid.uuid4())


class TestSchedulerHistoryService:
    """Test cases for SchedulerHistoryService."""

    @pytest.mark.asyncio
    async def test_track_step_success(
        self,
        service: SchedulerHistoryService,
        sample_session_id: SessionId,
    ) -> None:
        """Test tracking a successful step execution."""
        step = SchedulerExecutionStep.SCHEDULE
        history_id = uuid.uuid4()

        with patch.object(
            service._repository, "record_step_start", new_callable=AsyncMock
        ) as mock_start, patch.object(
            service._repository, "record_step_success", new_callable=AsyncMock
        ) as mock_success:
            mock_start.return_value = history_id

            async with service.track_step(sample_session_id, step) as returned_id:
                assert returned_id == history_id
                # Simulate successful operation (no exception)

            mock_start.assert_called_once_with(sample_session_id, step, details=None)
            mock_success.assert_called_once_with(history_id)

    @pytest.mark.asyncio
    async def test_track_step_failure(
        self,
        service: SchedulerHistoryService,
        sample_session_id: SessionId,
    ) -> None:
        """Test tracking a failed step execution."""
        step = SchedulerExecutionStep.START
        history_id = uuid.uuid4()

        with patch.object(
            service._repository, "record_step_start", new_callable=AsyncMock
        ) as mock_start, patch.object(
            service._repository, "record_step_failure", new_callable=AsyncMock
        ) as mock_failure:
            mock_start.return_value = history_id

            with pytest.raises(ValueError):
                async with service.track_step(sample_session_id, step):
                    raise ValueError("Test error")

            mock_start.assert_called_once()
            mock_failure.assert_called_once()
            call_kwargs = mock_failure.call_args[1]
            assert call_kwargs["error_info"]["type"] == "ValueError"
            assert "Test error" in call_kwargs["error_info"]["message"]

    @pytest.mark.asyncio
    async def test_track_step_with_details(
        self,
        service: SchedulerHistoryService,
        sample_session_id: SessionId,
    ) -> None:
        """Test tracking step with additional details."""
        step = SchedulerExecutionStep.SCHEDULE
        details = {"scaling_group": "gpu-cluster", "pending_sessions": 10}
        history_id = uuid.uuid4()

        with patch.object(
            service._repository, "record_step_start", new_callable=AsyncMock
        ) as mock_start, patch.object(
            service._repository, "record_step_success", new_callable=AsyncMock
        ):
            mock_start.return_value = history_id

            async with service.track_step(sample_session_id, step, details=details):
                pass

            mock_start.assert_called_once_with(sample_session_id, step, details=details)

    @pytest.mark.asyncio
    async def test_record_step_retry(
        self,
        service: SchedulerHistoryService,
        sample_session_id: SessionId,
    ) -> None:
        """Test recording a retry attempt."""
        step = SchedulerExecutionStep.CHECK_PULLING_PROGRESS
        history_id = uuid.uuid4()

        with patch.object(
            service._repository, "record_step_retry", new_callable=AsyncMock
        ) as mock_retry:
            mock_retry.return_value = history_id

            result = await service.record_step_retry(sample_session_id, step)

            assert result == history_id
            mock_retry.assert_called_once_with(sample_session_id, step)

    @pytest.mark.asyncio
    async def test_get_session_history(
        self,
        service: SchedulerHistoryService,
        sample_session_id: SessionId,
    ) -> None:
        """Test retrieving session history."""
        mock_history = [
            MagicMock(spec=SchedulerExecutionHistoryRow),
            MagicMock(spec=SchedulerExecutionHistoryRow),
        ]

        with patch.object(
            service._repository, "get_session_history", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_history

            history = await service.get_session_history(sample_session_id)

            assert len(history) == 2
            mock_get.assert_called_once_with(sample_session_id)

    @pytest.mark.asyncio
    async def test_get_step_summary(
        self,
        service: SchedulerHistoryService,
        sample_session_id: SessionId,
    ) -> None:
        """Test getting step execution summary."""
        now = datetime.now(timezone.utc)
        mock_history = [
            MagicMock(
                step=SchedulerExecutionStep.SCHEDULE,
                status=SchedulerExecutionStatus.SUCCESS,
                started_at=now - timedelta(seconds=10),
                finished_at=now - timedelta(seconds=9),
                retry_count=0,
                error_info=None,
                details={"scaling_group": "default"},
            ),
            MagicMock(
                step=SchedulerExecutionStep.START,
                status=SchedulerExecutionStatus.FAILURE,
                started_at=now - timedelta(seconds=8),
                finished_at=now - timedelta(seconds=7),
                retry_count=2,
                error_info={"type": "AgentError", "message": "Connection refused"},
                details=None,
            ),
        ]

        with patch.object(
            service._repository, "get_session_history", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_history

            summary = await service.get_step_summary(sample_session_id)

            assert summary["session_id"] == str(sample_session_id)
            assert summary["total_steps"] == 2
            assert len(summary["steps"]) == 2

            # Check first step
            first_step = summary["steps"][0]
            assert first_step["step"] == "SCHEDULE"
            assert first_step["status"] == "SUCCESS"
            assert first_step["retry_count"] == 0
            assert first_step["duration_seconds"] == pytest.approx(1.0, rel=0.1)
            assert first_step["details"] == {"scaling_group": "default"}

            # Check second step
            second_step = summary["steps"][1]
            assert second_step["step"] == "START"
            assert second_step["status"] == "FAILURE"
            assert second_step["retry_count"] == 2
            assert "error_info" in second_step

            # Check statistics
            stats = summary["statistics"]
            assert stats["total_retries"] == 2
            assert stats["failed_steps"] == 1
            assert stats["successful_steps"] == 1
            assert stats["in_progress_steps"] == 0

    @pytest.mark.asyncio
    async def test_get_step_summary_empty_history(
        self,
        service: SchedulerHistoryService,
        sample_session_id: SessionId,
    ) -> None:
        """Test summary with no history."""
        with patch.object(
            service._repository, "get_session_history", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = []

            summary = await service.get_step_summary(sample_session_id)

            assert summary["total_steps"] == 0
            assert len(summary["steps"]) == 0
            assert summary["statistics"]["total_retries"] == 0
            assert summary["statistics"]["failed_steps"] == 0
            assert summary["statistics"]["successful_steps"] == 0

    @pytest.mark.asyncio
    async def test_get_step_summary_with_in_progress(
        self,
        service: SchedulerHistoryService,
        sample_session_id: SessionId,
    ) -> None:
        """Test summary with in-progress steps."""
        now = datetime.now(timezone.utc)
        mock_history = [
            MagicMock(
                step=SchedulerExecutionStep.SCHEDULE,
                status=SchedulerExecutionStatus.IN_PROGRESS,
                started_at=now,
                finished_at=None,
                retry_count=0,
                error_info=None,
                details=None,
            ),
        ]

        with patch.object(
            service._repository, "get_session_history", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_history

            summary = await service.get_step_summary(sample_session_id)

            step = summary["steps"][0]
            assert step["status"] == "IN_PROGRESS"
            assert step["duration_seconds"] is None  # Not finished yet

            stats = summary["statistics"]
            assert stats["in_progress_steps"] == 1
            assert stats["successful_steps"] == 0
            assert stats["failed_steps"] == 0


class TestSchedulerHistoryServiceManualMethods:
    """Test cases for manual recording methods."""

    @pytest.mark.asyncio
    async def test_record_step_start(
        self,
        service: SchedulerHistoryService,
        sample_session_id: SessionId,
    ) -> None:
        """Test manual step start recording."""
        step = SchedulerExecutionStep.TERMINATE
        history_id = uuid.uuid4()

        with patch.object(
            service._repository, "record_step_start", new_callable=AsyncMock
        ) as mock_start:
            mock_start.return_value = history_id

            result = await service.record_step_start(sample_session_id, step)

            assert result == history_id
            mock_start.assert_called_once_with(sample_session_id, step, details=None)

    @pytest.mark.asyncio
    async def test_record_step_success_manual(
        self,
        service: SchedulerHistoryService,
    ) -> None:
        """Test manual success recording."""
        history_id = uuid.uuid4()
        details = {"cleanup_complete": True}

        with patch.object(
            service._repository, "record_step_success", new_callable=AsyncMock
        ) as mock_success:
            await service.record_step_success(history_id, details=details)

            mock_success.assert_called_once_with(history_id, details=details)

    @pytest.mark.asyncio
    async def test_record_step_failure_manual(
        self,
        service: SchedulerHistoryService,
    ) -> None:
        """Test manual failure recording."""
        history_id = uuid.uuid4()
        error_info = {"type": "TimeoutError", "message": "Operation timed out"}

        with patch.object(
            service._repository, "record_step_failure", new_callable=AsyncMock
        ) as mock_failure:
            await service.record_step_failure(history_id, error_info=error_info)

            mock_failure.assert_called_once_with(
                history_id, error_info=error_info, details=None
            )
