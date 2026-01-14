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
from aiohttp.multipart import BodyPartReader
from dateutil.tz import tzutc

from ai.backend.common.dto.agent.response import CodeCompletionResp, CodeCompletionResult
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import (
    ClusterConfig,
    ImageInfo,
    KernelInfo,
    KernelListResult,
    KernelStatus,
    LifecycleStatus,
    Metadata,
    Metrics,
    NetworkConfig,
    RelatedSessionInfo,
    ResourceInfo,
    RuntimeConfig,
    UserPermission,
)
from ai.backend.manager.data.session.types import SessionData, SessionListResult, SessionStatus
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.errors.storage import VFolderBadRequest
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.scheduler import MarkTerminatingResult
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.session.actions.check_and_transit_status import (
    CheckAndTransitStatusAction,
    CheckAndTransitStatusActionResult,
)
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
from ai.backend.manager.services.session.actions.execute_session import (
    ExecuteSessionAction,
    ExecuteSessionActionParams,
    ExecuteSessionActionResult,
)
from ai.backend.manager.services.session.actions.get_container_logs import (
    GetContainerLogsAction,
    GetContainerLogsActionResult,
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
from ai.backend.manager.services.session.actions.interrupt_session import (
    InterruptSessionAction,
    InterruptSessionActionResult,
)
from ai.backend.manager.services.session.actions.list_files import (
    ListFilesAction,
    ListFilesActionResult,
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
from ai.backend.manager.services.session.actions.search import SearchSessionsAction
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction
from ai.backend.manager.services.session.actions.shutdown_service import (
    ShutdownServiceAction,
    ShutdownServiceActionResult,
)
from ai.backend.manager.services.session.actions.upload_files import (
    UploadFilesAction,
    UploadFilesActionResult,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs

# ==================== Shared Fixtures ====================


@pytest.fixture
def mock_session_repository() -> MagicMock:
    """Create mocked session repository."""
    return MagicMock(spec=SessionRepository)


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
def sample_user_id() -> UUID:
    """Create sample user ID."""
    return uuid4()


@pytest.fixture
def sample_group_id() -> UUID:
    """Create sample group ID."""
    return uuid4()


@pytest.fixture
def sample_session_data(
    sample_session_id: SessionId,
    sample_access_key: AccessKey,
    sample_user_id: UUID,
    sample_group_id: UUID,
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
        group_id=sample_group_id,
        user_uuid=sample_user_id,
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
        sample_user_id: UUID,
        sample_group_id: UUID,
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
                group_id=sample_group_id,
                user_uuid=sample_user_id,
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
        """Test getting empty status history returns empty dict when None"""
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
        assert result.status_history == {}


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
        sample_user_id: UUID,
        sample_group_id: UUID,
    ) -> None:
        """Test successfully getting session info"""
        # Create a mock session with main_kernel
        mock_kernel = MagicMock()
        mock_kernel.image = "cr.backend.ai/stable/python:latest"
        mock_kernel.architecture = "x86_64"
        mock_kernel.registry = "cr.backend.ai"
        mock_kernel.container_id = str(uuid4())
        mock_kernel.occupied_slots = ResourceSlot({"cpu": 1, "mem": 1024})
        mock_kernel.occupied_shares = {}

        mock_session = MagicMock()
        mock_session.id = sample_session_id
        mock_session.domain_name = "default"
        mock_session.group_id = sample_group_id
        mock_session.user_uuid = sample_user_id
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
        sample_user_id: UUID,
    ) -> None:
        """Test successfully downloading files"""
        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.download_file = AsyncMock(return_value=b"file content")

        action = DownloadFilesAction(
            user_id=sample_user_id,
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
        sample_user_id: UUID,
    ) -> None:
        """Test downloading files when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = DownloadFilesAction(
            user_id=sample_user_id,
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
        sample_user_id: UUID,
    ) -> None:
        """Test downloading too many files raises error"""
        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = DownloadFilesAction(
            user_id=sample_user_id,
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
        sample_user_id: UUID,
    ) -> None:
        """Test successfully listing files"""
        expected_files = {"files": ["file1.txt", "file2.py"]}

        mock_session = MagicMock()
        mock_session.to_dataclass.return_value = sample_session_data
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.list_files = AsyncMock(return_value=expected_files)

        action = ListFilesAction(
            user_id=sample_user_id,
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
        sample_user_id: UUID,
    ) -> None:
        """Test listing files when session not found"""
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = ListFilesAction(
            user_id=sample_user_id,
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

        action = GetContainerLogsAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
            kernel_id=None,
        )

        with pytest.raises(SessionNotFound):
            await session_service.get_container_logs(action)


# ==================== CheckAndTransitStatus Tests ====================


@pytest.mark.asyncio
class TestCheckAndTransitStatus:
    """Test cases for SessionService.check_and_transit_status"""

    @pytest.fixture
    def other_user_id(self) -> UUID:
        """Create another user ID for ownership tests."""
        return uuid4()

    @pytest.fixture
    def mock_session_for_transit(self, sample_session_id: SessionId) -> MagicMock:
        """Create a mock session for transit status tests."""
        mock_session = MagicMock()
        mock_session.id = sample_session_id
        mock_session.status = SessionStatus.RUNNING
        mock_session.to_dataclass.return_value = MagicMock()
        return mock_session

    @pytest.fixture
    def setup_transit_mocks(
        self,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        mock_session_for_transit: MagicMock,
    ) -> MagicMock:
        """Setup common mocks for transit status tests that expect successful transit."""
        mock_session_repository.get_session_by_id = AsyncMock(return_value=mock_session_for_transit)
        mock_session_repository.get_session_owner = AsyncMock(return_value=None)

        mock_agent_registry.session_lifecycle_mgr = MagicMock()
        mock_agent_registry.session_lifecycle_mgr.transit_session_status = AsyncMock(
            return_value=[(mock_session_for_transit, True)]
        )
        mock_agent_registry.session_lifecycle_mgr.deregister_status_updatable_session = AsyncMock()

        return mock_session_for_transit

    async def test_check_and_transit_status_as_superadmin_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_user_id: UUID,
        other_user_id: UUID,
        setup_transit_mocks: MagicMock,
    ) -> None:
        """Test SUPERADMIN can transit status of other user's session."""
        setup_transit_mocks.user_uuid = other_user_id  # Different user owns the session

        action = CheckAndTransitStatusAction(
            user_id=sample_user_id,
            user_role=UserRole.SUPERADMIN,
            session_id=sample_session_id,
        )
        result = await session_service.check_and_transit_status(action)

        assert isinstance(result, CheckAndTransitStatusActionResult)
        assert sample_session_id in result.result
        mock_session_repository.get_session_by_id.assert_called_once_with(sample_session_id)

    async def test_check_and_transit_status_as_admin_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_user_id: UUID,
        other_user_id: UUID,
        setup_transit_mocks: MagicMock,
    ) -> None:
        """Test ADMIN can transit status of other user's session."""
        setup_transit_mocks.user_uuid = other_user_id  # Different user owns the session

        action = CheckAndTransitStatusAction(
            user_id=sample_user_id,
            user_role=UserRole.ADMIN,
            session_id=sample_session_id,
        )
        result = await session_service.check_and_transit_status(action)

        assert isinstance(result, CheckAndTransitStatusActionResult)
        assert sample_session_id in result.result
        mock_session_repository.get_session_by_id.assert_called_once_with(sample_session_id)

    async def test_check_and_transit_status_as_user_own_session_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_user_id: UUID,
        setup_transit_mocks: MagicMock,
    ) -> None:
        """Test USER can transit status of their own session."""
        setup_transit_mocks.user_uuid = sample_user_id  # Same user owns the session

        action = CheckAndTransitStatusAction(
            user_id=sample_user_id,
            user_role=UserRole.USER,
            session_id=sample_session_id,
        )
        result = await session_service.check_and_transit_status(action)

        assert isinstance(result, CheckAndTransitStatusActionResult)
        assert sample_session_id in result.result
        mock_session_repository.get_session_by_id.assert_called_once_with(sample_session_id)

    async def test_check_and_transit_status_as_user_other_session_skipped(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_user_id: UUID,
        other_user_id: UUID,
        mock_session_for_transit: MagicMock,
    ) -> None:
        """Test USER cannot transit status of other user's session (returns empty result)."""
        mock_session_for_transit.user_uuid = other_user_id  # Different user owns the session
        mock_session_repository.get_session_by_id = AsyncMock(return_value=mock_session_for_transit)

        action = CheckAndTransitStatusAction(
            user_id=sample_user_id,
            user_role=UserRole.USER,
            session_id=sample_session_id,
        )
        result = await session_service.check_and_transit_status(action)

        assert isinstance(result, CheckAndTransitStatusActionResult)
        # Result should be empty when user tries to transit other's session
        assert result.result == {}
        mock_session_repository.get_session_by_id.assert_called_once_with(sample_session_id)
        # transit_session_status should NOT be called
        mock_agent_registry.session_lifecycle_mgr.transit_session_status.assert_not_called()

    async def test_check_and_transit_status_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_user_id: UUID,
    ) -> None:
        """Test check_and_transit_status raises SessionNotFound for non-existent session."""
        mock_session_repository.get_session_by_id = AsyncMock(return_value=None)

        action = CheckAndTransitStatusAction(
            user_id=sample_user_id,
            user_role=UserRole.SUPERADMIN,
            session_id=sample_session_id,
        )

        with pytest.raises(SessionNotFound):
            await session_service.check_and_transit_status(action)


# ==================== Search Tests ====================


@pytest.mark.asyncio
class TestSearch:
    """Test cases for SessionService.search"""

    async def test_search_sessions(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_data: SessionData,
    ) -> None:
        """Test searching sessions with querier"""
        mock_session_repository.search = AsyncMock(
            return_value=SessionListResult(
                items=[sample_session_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchSessionsAction(querier=querier)
        result = await session_service.search(action)

        assert result.data == [sample_session_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_session_repository.search.assert_called_once_with(querier)

    async def test_search_sessions_empty_result(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
    ) -> None:
        """Test searching sessions when no results are found"""
        mock_session_repository.search = AsyncMock(
            return_value=SessionListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchSessionsAction(querier=querier)
        result = await session_service.search(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_sessions_with_pagination(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_data: SessionData,
    ) -> None:
        """Test searching sessions with pagination"""
        mock_session_repository.search = AsyncMock(
            return_value=SessionListResult(
                items=[sample_session_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchSessionsAction(querier=querier)
        result = await session_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True


# ==================== SearchKernels Tests ====================


@pytest.mark.asyncio
class TestSearchKernels:
    """Test cases for SessionService.search_kernels"""

    @pytest.fixture
    def sample_kernel_info(self) -> KernelInfo:
        """Create sample kernel info data"""
        kernel_id = KernelId(uuid4())
        session_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()

        return KernelInfo(
            id=kernel_id,
            session=RelatedSessionInfo(
                session_id=str(session_id),
                creation_id="test-creation-id",
                name="test-session",
                session_type=SessionTypes.INTERACTIVE,
            ),
            user_permission=UserPermission(
                user_uuid=user_id,
                access_key="TESTKEY",
                domain_name="default",
                group_id=group_id,
                uid=1000,
                main_gid=1000,
                gids=[1000],
            ),
            image=ImageInfo(
                identifier=None,
                registry="cr.backend.ai",
                tag="latest",
                architecture="x86_64",
            ),
            network=NetworkConfig(
                kernel_host="localhost",
                repl_in_port=2000,
                repl_out_port=2001,
                stdin_port=2002,
                stdout_port=2003,
                service_ports=None,
                preopen_ports=None,
                use_host_network=False,
            ),
            cluster=ClusterConfig(
                cluster_mode="single-node",
                cluster_size=1,
                cluster_role="main",
                cluster_idx=0,
                local_rank=0,
                cluster_hostname="main",
            ),
            resource=ResourceInfo(
                scaling_group="default",
                agent="test-agent",
                agent_addr="localhost:6001",
                container_id="container-123",
                occupied_slots=ResourceSlot({"cpu": "1", "mem": "1G"}),
                requested_slots=ResourceSlot({"cpu": "1", "mem": "1G"}),
                occupied_shares={},
                attached_devices={},
                resource_opts={},
            ),
            runtime=RuntimeConfig(
                environ=None,
                mounts=None,
                mount_map=None,
                vfolder_mounts=None,
                bootstrap_script=None,
                startup_command=None,
            ),
            lifecycle=LifecycleStatus(
                status=KernelStatus.RUNNING,
                result=SessionResult.UNDEFINED,
                created_at=datetime.now(tzutc()),
                terminated_at=None,
                starts_at=None,
                status_changed=datetime.now(tzutc()),
                status_info=None,
                status_data=None,
                status_history=None,
                last_seen=datetime.now(tzutc()),
            ),
            metrics=Metrics(
                num_queries=0,
                last_stat=None,
                container_log=None,
            ),
            metadata=Metadata(
                callback_url=None,
                internal_data=None,
            ),
        )

    async def test_search_kernels(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_kernel_info: KernelInfo,
    ) -> None:
        """Test searching kernels with querier"""
        mock_session_repository.search_kernels = AsyncMock(
            return_value=KernelListResult(
                items=[sample_kernel_info],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchKernelsAction(querier=querier)
        result = await session_service.search_kernels(action)

        assert result.data == [sample_kernel_info]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_session_repository.search_kernels.assert_called_once_with(querier)

    async def test_search_kernels_empty_result(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
    ) -> None:
        """Test searching kernels when no results are found"""
        mock_session_repository.search_kernels = AsyncMock(
            return_value=KernelListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchKernelsAction(querier=querier)
        result = await session_service.search_kernels(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_kernels_with_pagination(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_kernel_info: KernelInfo,
    ) -> None:
        """Test searching kernels with pagination"""
        mock_session_repository.search_kernels = AsyncMock(
            return_value=KernelListResult(
                items=[sample_kernel_info],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchKernelsAction(querier=querier)
        result = await session_service.search_kernels(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True
