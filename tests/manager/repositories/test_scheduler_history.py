from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import SessionId
from ai.backend.manager.models.scheduler_history import (
    SchedulerExecutionHistoryRow,
    SchedulerExecutionStatus,
    SchedulerExecutionStep,
)
from ai.backend.manager.repositories.scheduler_history import SchedulerHistoryRepository


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=SASession)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def repository(mock_db_session: AsyncMock) -> SchedulerHistoryRepository:
    """Create a repository instance with mock session."""
    return SchedulerHistoryRepository(mock_db_session)


@pytest.fixture
def sample_session_id() -> SessionId:
    """Create a sample session ID."""
    return SessionId(uuid.uuid4())


class TestSchedulerHistoryRepository:
    """Test cases for SchedulerHistoryRepository."""

    @pytest.mark.asyncio
    async def test_record_step_start(
        self,
        repository: SchedulerHistoryRepository,
        mock_db_session: AsyncMock,
        sample_session_id: SessionId,
    ) -> None:
        """Test recording the start of a scheduler step."""
        step = SchedulerExecutionStep.SCHEDULE
        details = {"scaling_group": "default"}

        # Call the method
        history_id = await repository.record_step_start(
            sample_session_id, step, details=details
        )

        # Verify return value
        assert history_id is not None

        # Verify session.add was called with correct row
        mock_db_session.add.assert_called_once()
        added_row = mock_db_session.add.call_args[0][0]

        assert isinstance(added_row, SchedulerExecutionHistoryRow)
        assert added_row.session_id == sample_session_id
        assert added_row.step == step
        assert added_row.status == SchedulerExecutionStatus.IN_PROGRESS
        assert added_row.details == details
        assert added_row.retry_count == 0

        # Verify flush was called
        mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_step_success(
        self,
        repository: SchedulerHistoryRepository,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test marking a step as successful."""
        history_id = uuid.uuid4()
        details = {"selected_agent": "agent-001"}

        await repository.record_step_success(history_id, details=details)

        # Verify execute was called with update statement
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0][0]

        # Check it's an update statement
        assert isinstance(call_args, sa.sql.Update)
        assert "scheduler_execution_history" in str(call_args)

    @pytest.mark.asyncio
    async def test_record_step_failure(
        self,
        repository: SchedulerHistoryRepository,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test marking a step as failed."""
        history_id = uuid.uuid4()
        error_info = {
            "type": "ResourceUnavailableError",
            "message": "No available agents",
        }

        await repository.record_step_failure(history_id, error_info=error_info)

        # Verify execute was called
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0][0]

        assert isinstance(call_args, sa.sql.Update)

    @pytest.mark.asyncio
    async def test_record_step_retry(
        self,
        repository: SchedulerHistoryRepository,
        mock_db_session: AsyncMock,
        sample_session_id: SessionId,
    ) -> None:
        """Test recording a retry attempt."""
        step = SchedulerExecutionStep.START

        # Mock the query result
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_row)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result_id = await repository.record_step_retry(sample_session_id, step)

        assert result_id == mock_row.id
        # Verify two execute calls: one for select, one for update
        assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_record_step_retry_no_existing_record(
        self,
        repository: SchedulerHistoryRepository,
        mock_db_session: AsyncMock,
        sample_session_id: SessionId,
    ) -> None:
        """Test retry when no existing record found."""
        step = SchedulerExecutionStep.START

        # Mock empty result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result_id = await repository.record_step_retry(sample_session_id, step)

        assert result_id is None
        # Only one execute call for select
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_history(
        self,
        repository: SchedulerHistoryRepository,
        mock_db_session: AsyncMock,
        sample_session_id: SessionId,
    ) -> None:
        """Test retrieving session history."""
        # Mock history rows
        mock_rows = [
            MagicMock(spec=SchedulerExecutionHistoryRow),
            MagicMock(spec=SchedulerExecutionHistoryRow),
        ]
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_rows)
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        history = await repository.get_session_history(sample_session_id)

        assert len(history) == 2
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_step_history(
        self,
        repository: SchedulerHistoryRepository,
        mock_db_session: AsyncMock,
        sample_session_id: SessionId,
    ) -> None:
        """Test getting the latest history for a specific step."""
        step = SchedulerExecutionStep.SCHEDULE

        mock_row = MagicMock(spec=SchedulerExecutionHistoryRow)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_row)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await repository.get_latest_step_history(sample_session_id, step)

        assert result == mock_row

    @pytest.mark.asyncio
    async def test_get_in_progress_steps(
        self,
        repository: SchedulerHistoryRepository,
        mock_db_session: AsyncMock,
        sample_session_id: SessionId,
    ) -> None:
        """Test getting in-progress steps."""
        mock_rows = [MagicMock(spec=SchedulerExecutionHistoryRow)]
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_rows)
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        in_progress = await repository.get_in_progress_steps(sample_session_id)

        assert len(in_progress) == 1


class TestSchedulerExecutionHistoryRow:
    """Test cases for the model class."""

    def test_model_initialization(self) -> None:
        """Test creating a history row."""
        session_id = SessionId(uuid.uuid4())
        step = SchedulerExecutionStep.SCHEDULE
        details = {"key": "value"}

        row = SchedulerExecutionHistoryRow(
            session_id=session_id,
            step=step,
            details=details,
        )

        assert row.session_id == session_id
        assert row.step == step
        assert row.status == SchedulerExecutionStatus.IN_PROGRESS
        assert row.details == details
        assert row.retry_count == 0
        assert row.error_info is None
        assert row.finished_at is None
        assert row.last_retry_at is None

    def test_model_with_error_info(self) -> None:
        """Test creating a history row with error info."""
        session_id = SessionId(uuid.uuid4())
        step = SchedulerExecutionStep.START
        error_info = {
            "type": "KernelCreationFailed",
            "message": "Agent unreachable",
        }

        row = SchedulerExecutionHistoryRow(
            session_id=session_id,
            step=step,
            status=SchedulerExecutionStatus.FAILURE,
            error_info=error_info,
        )

        assert row.status == SchedulerExecutionStatus.FAILURE
        assert row.error_info == error_info

    def test_model_repr(self) -> None:
        """Test string representation."""
        session_id = SessionId(uuid.uuid4())
        row = SchedulerExecutionHistoryRow(
            session_id=session_id,
            step=SchedulerExecutionStep.SCHEDULE,
        )

        repr_str = repr(row)
        assert "SchedulerExecutionHistoryRow" in repr_str
        assert str(session_id) in repr_str
        assert "SCHEDULE" in repr_str


class TestSchedulerExecutionStep:
    """Test cases for the step enum."""

    def test_all_steps_defined(self) -> None:
        """Test that all required steps are defined."""
        expected_steps = [
            "SCHEDULE",
            "CHECK_PRECONDITION",
            "CHECK_PULLING_PROGRESS",
            "START",
            "CHECK_CREATING_PROGRESS",
            "TERMINATE",
            "CHECK_TERMINATING_PROGRESS",
            "SWEEP",
            "RETRY_PREPARING",
            "RETRY_CREATING",
        ]

        for step_name in expected_steps:
            assert hasattr(SchedulerExecutionStep, step_name)
            step = getattr(SchedulerExecutionStep, step_name)
            assert step.value == step_name

    def test_step_is_string_enum(self) -> None:
        """Test that step enum values are strings."""
        step = SchedulerExecutionStep.SCHEDULE
        assert isinstance(step.value, str)
        assert str(step) == "SCHEDULE"


class TestSchedulerExecutionStatus:
    """Test cases for the status enum."""

    def test_all_statuses_defined(self) -> None:
        """Test that all statuses are defined."""
        expected_statuses = ["IN_PROGRESS", "SUCCESS", "FAILURE"]

        for status_name in expected_statuses:
            assert hasattr(SchedulerExecutionStatus, status_name)
            status = getattr(SchedulerExecutionStatus, status_name)
            assert status.value == status_name
