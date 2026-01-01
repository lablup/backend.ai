"""
Unit tests for SessionService.
Tests the service layer with mocked repositories.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.repositories.session.admin_repository import AdminSessionRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.session.actions.get_status_history import (
    GetStatusHistoryAction,
)
from ai.backend.manager.services.session.actions.match_sessions import MatchSessionsAction
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs

# ==================== Shared Fixtures ====================


@pytest.fixture
def mock_session_repository() -> MagicMock:
    """Create mocked session repository."""
    return MagicMock(spec=SessionRepository)


@pytest.fixture
def mock_admin_session_repository() -> MagicMock:
    """Create mocked admin session repository."""
    return MagicMock(spec=AdminSessionRepository)


@pytest.fixture
def mock_agent_registry() -> MagicMock:
    """Create mocked agent registry."""
    mock = MagicMock()
    mock.increment_session_usage = AsyncMock()
    return mock


@pytest.fixture
def mock_event_fetcher() -> MagicMock:
    """Create mocked event fetcher."""
    return MagicMock()


@pytest.fixture
def mock_background_task_manager() -> MagicMock:
    """Create mocked background task manager."""
    return MagicMock()


@pytest.fixture
def mock_event_hub() -> MagicMock:
    """Create mocked event hub."""
    return MagicMock()


@pytest.fixture
def mock_error_monitor() -> MagicMock:
    """Create mocked error monitor."""
    return MagicMock()


@pytest.fixture
def mock_idle_checker_host() -> MagicMock:
    """Create mocked idle checker host."""
    mock = MagicMock()
    mock.get_idle_check_report = AsyncMock(return_value={})
    return mock


@pytest.fixture
def mock_scheduling_controller() -> MagicMock:
    """Create mocked scheduling controller."""
    return MagicMock()


@pytest.fixture
async def session_service(
    mock_session_repository: MagicMock,
    mock_admin_session_repository: MagicMock,
    mock_agent_registry: MagicMock,
    mock_event_fetcher: MagicMock,
    mock_background_task_manager: MagicMock,
    mock_event_hub: MagicMock,
    mock_error_monitor: MagicMock,
    mock_idle_checker_host: MagicMock,
    mock_scheduling_controller: MagicMock,
) -> SessionService:
    """Create SessionService with mocked dependencies."""
    args = SessionServiceArgs(
        agent_registry=mock_agent_registry,
        event_fetcher=mock_event_fetcher,
        background_task_manager=mock_background_task_manager,
        event_hub=mock_event_hub,
        error_monitor=mock_error_monitor,
        idle_checker_host=mock_idle_checker_host,
        session_repository=mock_session_repository,
        admin_session_repository=mock_admin_session_repository,
        scheduling_controller=mock_scheduling_controller,
    )
    return SessionService(args)


@pytest.fixture
def sample_session_id() -> SessionId:
    """Create sample session ID."""
    return SessionId(uuid4())


@pytest.fixture
def sample_access_key() -> AccessKey:
    """Create sample access key."""
    return AccessKey("AKIAIOSFODNN7EXAMPLE")


@pytest.fixture
def sample_session_data(
    sample_session_id: SessionId,
    sample_access_key: AccessKey,
) -> SessionData:
    """Create sample session data."""
    return SessionData(
        id=sample_session_id,
        creation_id="test-creation-id",
        name="test-session",
        session_type=SessionTypes.INTERACTIVE,
        priority=0,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        agent_ids=["i-ubuntu"],
        domain_name="default",
        group_id=UUID("2de2b969-1d04-48a6-af16-0bc8adb3c831"),
        user_uuid=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        access_key=sample_access_key,
        images=["cr.backend.ai/stable/python:latest"],
        tag=None,
        occupying_slots=ResourceSlot({"cpu": 1, "mem": 1024}),
        requested_slots=ResourceSlot({"cpu": 1, "mem": 1024}),
        vfolder_mounts=[],
        environ={},
        bootstrap_script=None,
        use_host_network=False,
        timeout=None,
        batch_timeout=None,
        created_at=datetime.now(tzutc()),
        terminated_at=None,
        starts_at=None,
        status=SessionStatus.RUNNING,
        status_info=None,
        status_data=None,
        status_history={"PENDING": "2023-01-01T00:00:00Z", "RUNNING": "2023-01-01T00:01:00Z"},
        startup_command=None,
        callback_url=None,
        result=SessionResult.UNDEFINED,
        num_queries=0,
        last_stat=None,
        scaling_group_name="default",
        target_sgroup_names=[],
        network_type=NetworkType.VOLATILE,
        network_id=None,
        owner=None,
        service_ports=None,
    )


# ==================== MatchSessions Tests ====================


@pytest.mark.asyncio
class TestMatchSessions:
    """Test cases for SessionService.match_sessions"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully matching sessions"""
        mock_session_repository.match_sessions = AsyncMock(return_value=[sample_session_data])

        action = MatchSessionsAction(
            id_or_name_prefix="test",
            owner_access_key=sample_access_key,
        )
        result = await session_service.match_sessions(action)

        assert len(result.result) == 1
        assert result.result[0]["id"] == str(sample_session_data.id)
        assert result.result[0]["name"] == sample_session_data.name
        assert result.result[0]["status"] == sample_session_data.status.name
        mock_session_repository.match_sessions.assert_called_once_with("test", sample_access_key)

    async def test_no_matches(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test matching sessions when none found"""
        mock_session_repository.match_sessions = AsyncMock(return_value=[])

        action = MatchSessionsAction(
            id_or_name_prefix="nonexistent",
            owner_access_key=sample_access_key,
        )
        result = await session_service.match_sessions(action)

        assert result.result == []

    async def test_multiple_matches(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test matching multiple sessions"""
        sessions = [
            SessionData(
                id=SessionId(uuid4()),
                creation_id=f"creation-{i}",
                name=f"test-session-{i}",
                session_type=SessionTypes.INTERACTIVE,
                priority=0,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                agent_ids=[],
                domain_name="default",
                group_id=UUID("2de2b969-1d04-48a6-af16-0bc8adb3c831"),
                user_uuid=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                access_key=sample_access_key,
                images=["python:latest"],
                tag=None,
                occupying_slots=ResourceSlot({}),
                requested_slots=ResourceSlot({}),
                vfolder_mounts=[],
                environ={},
                bootstrap_script=None,
                use_host_network=False,
                timeout=None,
                batch_timeout=None,
                created_at=datetime.now(tzutc()),
                terminated_at=None,
                starts_at=None,
                status=SessionStatus.RUNNING,
                status_info=None,
                status_data=None,
                status_history=None,
                startup_command=None,
                callback_url=None,
                result=SessionResult.UNDEFINED,
                num_queries=0,
                last_stat=None,
                scaling_group_name="default",
                target_sgroup_names=[],
                network_type=NetworkType.VOLATILE,
                network_id=None,
                owner=None,
                service_ports=None,
            )
            for i in range(3)
        ]
        mock_session_repository.match_sessions = AsyncMock(return_value=sessions)

        action = MatchSessionsAction(
            id_or_name_prefix="test",
            owner_access_key=sample_access_key,
        )
        result = await session_service.match_sessions(action)

        assert len(result.result) == 3
        for i, match in enumerate(result.result):
            assert match["name"] == f"test-session-{i}"


# ==================== GetStatusHistory Tests ====================


@pytest.mark.asyncio
class TestGetStatusHistory:
    """Test cases for SessionService.get_status_history"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully getting status history"""
        status_history: dict[str, Any] = {
            "PENDING": "2023-01-01T00:00:00Z",
            "SCHEDULED": "2023-01-01T00:00:30Z",
            "RUNNING": "2023-01-01T00:01:00Z",
        }

        mock_session = MagicMock()
        mock_session.id = sample_session_id
        mock_session.status_history = status_history
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = GetStatusHistoryAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_status_history(action)

        assert result.session_id == sample_session_id
        assert result.status_history == status_history
        mock_session_repository.get_session_validated.assert_called_once()

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test getting status history for non-existent session"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = GetStatusHistoryAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(SessionNotFound):
            await session_service.get_status_history(action)

    async def test_empty_status_history(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
    ) -> None:
        """Test getting empty status history"""
        mock_session = MagicMock()
        mock_session.id = sample_session_id
        mock_session.status_history = None
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = GetStatusHistoryAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_status_history(action)

        assert result.session_id == sample_session_id
        assert result.status_history is None
