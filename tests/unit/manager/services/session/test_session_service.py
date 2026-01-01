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

from ai.backend.common.dto.agent.response import CodeCompletionResp, CodeCompletionResult
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
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.scheduler import MarkTerminatingResult
from ai.backend.manager.repositories.session.admin_repository import AdminSessionRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.session.actions.complete import (
    CompleteAction,
    CompleteActionResult,
)
from ai.backend.manager.services.session.actions.destroy_session import (
    DestroySessionAction,
)
from ai.backend.manager.services.session.actions.download_files import (
    DownloadFilesAction,
    DownloadFilesActionResult,
)
from ai.backend.manager.services.session.actions.get_direct_access_info import (
    GetDirectAccessInfoAction,
    GetDirectAccessInfoActionResult,
)
from ai.backend.manager.services.session.actions.get_session_info import (
    GetSessionInfoAction,
    GetSessionInfoActionResult,
)
from ai.backend.manager.services.session.actions.get_status_history import (
    GetStatusHistoryAction,
)
from ai.backend.manager.services.session.actions.match_sessions import MatchSessionsAction
from ai.backend.manager.services.session.actions.rename_session import (
    RenameSessionAction,
    RenameSessionActionResult,
)
from ai.backend.manager.services.session.actions.restart_session import (
    RestartSessionAction,
    RestartSessionActionResult,
)
from ai.backend.manager.services.session.actions.shutdown_service import (
    ShutdownServiceAction,
    ShutdownServiceActionResult,
)
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


# ==================== DestroySession Tests ====================


@pytest.mark.asyncio
class TestDestroySession:
    """Test cases for SessionService.destroy_session"""

    async def test_success_cancelled(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully destroying session (cancelled status)"""
        mock_session_repository.get_target_session_ids = AsyncMock(return_value=[sample_session_id])
        mock_scheduling_controller.mark_sessions_for_termination = AsyncMock(
            return_value=MarkTerminatingResult(
                cancelled_sessions=[sample_session_id],
                terminating_sessions=[],
                skipped_sessions=[],
            )
        )

        action = DestroySessionAction(
            user_role=UserRole.USER,
            session_name="test-session",
            forced=False,
            recursive=False,
            owner_access_key=sample_access_key,
        )
        result = await session_service.destroy_session(action)

        assert result.result == {"stats": {"status": "cancelled"}}
        mock_session_repository.get_target_session_ids.assert_called_once_with(
            "test-session", sample_access_key, recursive=False
        )
        mock_scheduling_controller.mark_sessions_for_termination.assert_called_once()

    async def test_success_terminated(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully destroying session (terminated status)"""
        mock_session_repository.get_target_session_ids = AsyncMock(return_value=[sample_session_id])
        mock_scheduling_controller.mark_sessions_for_termination = AsyncMock(
            return_value=MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[sample_session_id],
                skipped_sessions=[],
            )
        )

        action = DestroySessionAction(
            user_role=UserRole.USER,
            session_name="test-session",
            forced=True,
            recursive=False,
            owner_access_key=sample_access_key,
        )
        result = await session_service.destroy_session(action)

        assert result.result == {"stats": {"status": "terminated"}}

    async def test_recursive_destroy(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test destroying sessions recursively"""
        session_ids = [SessionId(uuid4()) for _ in range(3)]
        mock_session_repository.get_target_session_ids = AsyncMock(return_value=session_ids)
        mock_scheduling_controller.mark_sessions_for_termination = AsyncMock(
            return_value=MarkTerminatingResult(
                cancelled_sessions=session_ids,
                terminating_sessions=[],
                skipped_sessions=[],
            )
        )

        action = DestroySessionAction(
            user_role=UserRole.USER,
            session_name="test-session",
            forced=False,
            recursive=True,
            owner_access_key=sample_access_key,
        )
        result = await session_service.destroy_session(action)

        mock_session_repository.get_target_session_ids.assert_called_once_with(
            "test-session", sample_access_key, recursive=True
        )
        assert result.result == {"stats": {"status": "cancelled"}}

    async def test_no_sessions_to_destroy(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test destroying when no sessions found"""
        mock_session_repository.get_target_session_ids = AsyncMock(return_value=[])
        mock_scheduling_controller.mark_sessions_for_termination = AsyncMock(
            return_value=MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[],
                skipped_sessions=[],
            )
        )

        action = DestroySessionAction(
            user_role=UserRole.USER,
            session_name="nonexistent",
            forced=False,
            recursive=False,
            owner_access_key=sample_access_key,
        )
        result = await session_service.destroy_session(action)

        assert result.result == {"stats": {}}


# ==================== Complete Tests ====================


@pytest.mark.asyncio
class TestComplete:
    """Test cases for SessionService.complete"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully completing code"""
        expected_response = CodeCompletionResp(
            result=CodeCompletionResult(
                status="finished",
                error=None,
                suggestions=["test_completion"],
            )
        )

        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.get_completions = AsyncMock(return_value=expected_response)

        action = CompleteAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
            code="print('Hello')",
            options=None,
        )
        result = await session_service.complete(action)

        assert isinstance(result, CompleteActionResult)
        assert result.session_data == sample_session_data
        assert result.result == expected_response
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.increment_session_usage.assert_called_once_with(mock_session)
        mock_agent_registry.get_completions.assert_called_once()

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test completing code when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = CompleteAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
            code="print('Hello')",
            options=None,
        )

        with pytest.raises(SessionNotFound):
            await session_service.complete(action)


# ==================== GetSessionInfo Tests ====================


@pytest.mark.asyncio
class TestGetSessionInfo:
    """Test cases for SessionService.get_session_info"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        mock_idle_checker_host: MagicMock,
        sample_session_data: SessionData,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully getting session info"""
        # Create a mock session with main_kernel
        mock_kernel = MagicMock()
        mock_kernel.image = "cr.backend.ai/stable/python:latest"
        mock_kernel.architecture = "x86_64"
        mock_kernel.registry = "cr.backend.ai"
        mock_kernel.container_id = uuid4()
        mock_kernel.occupied_slots = ResourceSlot({"cpu": 1, "mem": 1024})
        mock_kernel.occupied_shares = {}

        mock_session = MagicMock()
        mock_session.id = sample_session_id
        mock_session.domain_name = "default"
        mock_session.group_id = UUID("2de2b969-1d04-48a6-af16-0bc8adb3c831")
        mock_session.user_uuid = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")
        mock_session.tag = None
        mock_session.main_kernel = mock_kernel
        mock_session.occupying_slots = ResourceSlot({"cpu": 1, "mem": 1024})
        mock_session.requested_slots = ResourceSlot({"cpu": 1, "mem": 1024})
        mock_session.environ = {}
        mock_session.resource_opts = {}
        mock_session.status = SessionStatus.RUNNING
        mock_session.status_info = None
        mock_session.status_data = None
        mock_session.created_at = datetime.now(tzutc())
        mock_session.terminated_at = None
        mock_session.num_queries = 0
        mock_session.last_stat = None
        mock_session.to_dataclass.return_value = sample_session_data

        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_idle_checker_host.get_idle_check_report = AsyncMock(return_value={})

        action = GetSessionInfoAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_session_info(action)

        assert isinstance(result, GetSessionInfoActionResult)
        assert result.session_info is not None
        assert result.session_info.domain_name == "default"
        assert result.session_info.image == "cr.backend.ai/stable/python:latest"
        assert result.session_data == sample_session_data
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.increment_session_usage.assert_called_once_with(mock_session)

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test getting session info when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = GetSessionInfoAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(SessionNotFound):
            await session_service.get_session_info(action)


# ==================== DownloadFiles Tests ====================


@pytest.mark.asyncio
class TestDownloadFiles:
    """Test cases for SessionService.download_files"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully downloading files"""
        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.download_file = AsyncMock(return_value=b"file content")

        action = DownloadFilesAction(
            user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
            session_name="test-session",
            owner_access_key=sample_access_key,
            files=["test_file.txt"],
        )
        result = await session_service.download_files(action)

        assert isinstance(result, DownloadFilesActionResult)
        assert result.session_data == sample_session_data
        assert result.result is not None
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.increment_session_usage.assert_called_once_with(mock_session)
        mock_agent_registry.download_file.assert_called_once()

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test downloading files when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = DownloadFilesAction(
            user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
            session_name="nonexistent",
            owner_access_key=sample_access_key,
            files=["test_file.txt"],
        )

        with pytest.raises(SessionNotFound):
            await session_service.download_files(action)

    async def test_too_many_files(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test downloading too many files raises error"""
        from ai.backend.manager.errors.storage import VFolderBadRequest

        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = DownloadFilesAction(
            user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
            session_name="test-session",
            owner_access_key=sample_access_key,
            files=["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt", "file6.txt"],
        )

        with pytest.raises(VFolderBadRequest):
            await session_service.download_files(action)


# ==================== GetDirectAccessInfo Tests ====================


@pytest.mark.asyncio
class TestGetDirectAccessInfo:
    """Test cases for SessionService.get_direct_access_info"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully getting direct access info"""
        mock_session = MagicMock()
        mock_session.session_type = SessionTypes.INTERACTIVE
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = GetDirectAccessInfoAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_direct_access_info(action)

        assert isinstance(result, GetDirectAccessInfoActionResult)
        assert result.session_data == sample_session_data
        # For non-SYSTEM session types, result should be empty
        assert result.result == {}
        mock_session_repository.get_session_validated.assert_called_once()

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test getting direct access info when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = GetDirectAccessInfoAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(SessionNotFound):
            await session_service.get_direct_access_info(action)


# ==================== RenameSession Tests ====================


@pytest.mark.asyncio
class TestRenameSession:
    """Test cases for SessionService.rename_session"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully renaming session"""
        mock_session = MagicMock()
        mock_session.status = SessionStatus.RUNNING
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.update_session_name = AsyncMock(return_value=mock_session)

        action = RenameSessionAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
            new_name="new-session-name",
        )
        result = await session_service.rename_session(action)

        assert isinstance(result, RenameSessionActionResult)
        assert result.session_data == sample_session_data
        mock_session_repository.update_session_name.assert_called_once_with(
            "test-session", "new-session-name", sample_access_key
        )

    async def test_not_running_session(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test renaming non-running session raises error"""
        from ai.backend.common.exception import InvalidAPIParameters

        mock_session = MagicMock()
        mock_session.status = SessionStatus.PENDING  # Not running
        mock_session_repository.update_session_name = AsyncMock(return_value=mock_session)

        action = RenameSessionAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
            new_name="new-session-name",
        )

        with pytest.raises(InvalidAPIParameters):
            await session_service.rename_session(action)


# ==================== RestartSession Tests ====================


@pytest.mark.asyncio
class TestRestartSession:
    """Test cases for SessionService.restart_session"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully restarting session"""
        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.restart_session = AsyncMock()

        action = RestartSessionAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.restart_session(action)

        assert isinstance(result, RestartSessionActionResult)
        assert result.session_data == sample_session_data
        assert result.result is None
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.increment_session_usage.assert_called_once_with(mock_session)
        mock_agent_registry.restart_session.assert_called_once_with(mock_session)

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test restarting session when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = RestartSessionAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(SessionNotFound):
            await session_service.restart_session(action)


# ==================== ShutdownService Tests ====================


@pytest.mark.asyncio
class TestShutdownService:
    """Test cases for SessionService.shutdown_service"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully shutting down service"""
        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.shutdown_service = AsyncMock()

        action = ShutdownServiceAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
            service_name="test-service",
        )
        result = await session_service.shutdown_service(action)

        assert isinstance(result, ShutdownServiceActionResult)
        assert result.session_data == sample_session_data
        assert result.result is None
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.shutdown_service.assert_called_once_with(mock_session, "test-service")

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test shutting down service when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = ShutdownServiceAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
            service_name="test-service",
        )

        with pytest.raises(SessionNotFound):
            await session_service.shutdown_service(action)


# ==================== UploadFiles Tests ====================


@pytest.mark.asyncio
class TestUploadFiles:
    """Test cases for SessionService.upload_files"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully uploading files"""
        from aiohttp.multipart import BodyPartReader

        # Create a mock reader
        mock_file = MagicMock(spec=BodyPartReader)
        mock_file.filename = "test_file.txt"
        mock_file.read_chunk = AsyncMock(side_effect=[b"test content", b""])

        mock_reader = MagicMock()
        call_count = 0

        async def mock_next():
            nonlocal call_count
            if call_count == 0:
                call_count += 1
                return mock_file
            return None

        mock_reader.next = mock_next

        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.upload_file = AsyncMock()

        from ai.backend.manager.services.session.actions.upload_files import (
            UploadFilesAction,
            UploadFilesActionResult,
        )

        action = UploadFilesAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
            reader=mock_reader,
        )
        result = await session_service.upload_files(action)

        assert isinstance(result, UploadFilesActionResult)
        assert result.session_data == sample_session_data
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.increment_session_usage.assert_called_once_with(mock_session)

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test uploading files when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )
        mock_reader = MagicMock()
        mock_reader.next = AsyncMock(return_value=None)

        from ai.backend.manager.services.session.actions.upload_files import (
            UploadFilesAction,
        )

        action = UploadFilesAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
            reader=mock_reader,
        )

        with pytest.raises(SessionNotFound):
            await session_service.upload_files(action)


# ==================== Execute Tests ====================


@pytest.mark.asyncio
class TestExecute:
    """Test cases for SessionService.execute"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully executing code"""
        expected_execute_response = {
            "status": "finished",
            "runId": "test-run-id",
            "exitCode": 0,
            "options": {},
            "files": [],
            "console": [],
        }

        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.execute = AsyncMock(return_value=expected_execute_response)

        from ai.backend.manager.services.session.actions.execute_session import (
            ExecuteSessionAction,
            ExecuteSessionActionParams,
            ExecuteSessionActionResult,
        )

        params = ExecuteSessionActionParams(
            mode="query",
            options=None,
            code="print('Hello World')",
            run_id="test-run-id",
        )
        action = ExecuteSessionAction(
            session_name="test-session",
            api_version=(4, 0),
            owner_access_key=sample_access_key,
            params=params,
        )
        result = await session_service.execute_session(action)

        assert isinstance(result, ExecuteSessionActionResult)
        assert result.session_data == sample_session_data
        assert result.result is not None
        assert result.result["result"]["status"] == "finished"
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.increment_session_usage.assert_called_once_with(mock_session)
        mock_agent_registry.execute.assert_called_once()

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test executing code when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        from ai.backend.manager.services.session.actions.execute_session import (
            ExecuteSessionAction,
            ExecuteSessionActionParams,
        )

        params = ExecuteSessionActionParams(
            mode="query",
            options=None,
            code="print('Hello World')",
            run_id="test-run-id",
        )
        action = ExecuteSessionAction(
            session_name="nonexistent",
            api_version=(4, 0),
            owner_access_key=sample_access_key,
            params=params,
        )

        with pytest.raises(SessionNotFound):
            await session_service.execute_session(action)


# ==================== Interrupt Tests ====================


@pytest.mark.asyncio
class TestInterrupt:
    """Test cases for SessionService.interrupt"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully interrupting session"""
        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.interrupt_session = AsyncMock(return_value={})

        from ai.backend.manager.services.session.actions.interrupt_session import (
            InterruptSessionAction,
            InterruptSessionActionResult,
        )

        action = InterruptSessionAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.interrupt(action)

        assert isinstance(result, InterruptSessionActionResult)
        assert result.session_data == sample_session_data
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.increment_session_usage.assert_called_once_with(mock_session)
        mock_agent_registry.interrupt_session.assert_called_once_with(mock_session)

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test interrupting session when not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        from ai.backend.manager.services.session.actions.interrupt_session import (
            InterruptSessionAction,
        )

        action = InterruptSessionAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(SessionNotFound):
            await session_service.interrupt(action)


# ==================== ListFiles Tests ====================


@pytest.mark.asyncio
class TestListFiles:
    """Test cases for SessionService.list_files"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully listing files"""
        expected_files = {"files": ["file1.txt", "file2.py"]}

        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.list_files = AsyncMock(return_value=expected_files)

        from ai.backend.manager.services.session.actions.list_files import (
            ListFilesAction,
            ListFilesActionResult,
        )

        action = ListFilesAction(
            user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
            path="/home/work",
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.list_files(action)

        assert isinstance(result, ListFilesActionResult)
        assert result.session_data == sample_session_data
        assert result.result == expected_files
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.list_files.assert_called_once()

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test listing files when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        from ai.backend.manager.services.session.actions.list_files import (
            ListFilesAction,
        )

        action = ListFilesAction(
            user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
            path="/home/work",
            session_name="nonexistent",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(SessionNotFound):
            await session_service.list_files(action)


# ==================== GetContainerLogs Tests ====================


@pytest.mark.asyncio
class TestGetContainerLogs:
    """Test cases for SessionService.get_container_logs"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully getting container logs"""
        # get_logs_from_agent returns the logs directly
        agent_logs = {"stdout": "Hello World\\n", "stderr": ""}

        mock_session = MagicMock()
        mock_session.status = SessionStatus.RUNNING  # Not in DEAD_SESSION_STATUSES
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.get_logs_from_agent = AsyncMock(return_value=agent_logs)

        from ai.backend.manager.services.session.actions.get_container_logs import (
            GetContainerLogsAction,
            GetContainerLogsActionResult,
        )

        action = GetContainerLogsAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
            kernel_id=None,  # Optional - get logs from main kernel
        )
        result = await session_service.get_container_logs(action)

        assert isinstance(result, GetContainerLogsActionResult)
        assert result.session_data == sample_session_data
        # Result is wrapped as {"result": {"logs": <agent_logs>}}
        assert result.result["result"]["logs"] == agent_logs
        mock_session_repository.get_session_validated.assert_called_once()
        mock_agent_registry.get_logs_from_agent.assert_called_once()

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test getting logs when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        from ai.backend.manager.services.session.actions.get_container_logs import (
            GetContainerLogsAction,
        )

        action = GetContainerLogsAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
            kernel_id=None,
        )

        with pytest.raises(SessionNotFound):
            await session_service.get_container_logs(action)
