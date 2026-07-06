"""
Unit tests for SessionService.
Tests the service layer with mocked repositories.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from aiohttp.multipart import BodyPartReader
from dateutil.tz import tzutc

from ai.backend.common.dto.agent.response import CodeCompletionResp, CodeCompletionResult
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
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
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    ResourceSlotEntry,
    SessionResourceSpec,
    SessionSchedulingSpec,
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
from ai.backend.manager.services.session.actions.resolve_session_name import (
    ResolveSessionNameAction,
    ResolveSessionNameActionResult,
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
    return MagicMock()


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
def mock_scheduler_repository() -> MagicMock:
    """Create mocked scheduler repository."""
    return MagicMock()


@pytest.fixture
def mock_appproxy_client_pool() -> MagicMock:
    """Create mocked AppProxy client pool."""
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
    mock_scheduler_repository: MagicMock,
    mock_appproxy_client_pool: MagicMock,
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
        scheduler_repository=mock_scheduler_repository,
        scheduling_controller=mock_scheduling_controller,
        appproxy_client_pool=mock_appproxy_client_pool,
        user_repository=MagicMock(),
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
        is_preemptible=True,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        agent_ids=["i-ubuntu"],
        domain_name="default",
        group_id=sample_group_id,
        user_uuid=sample_user_id,
        access_key=sample_access_key,
        images=["cr.backend.ai/stable/python:latest"],
        image_ids=None,
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


class TestMatchSessions:
    """Test cases for SessionService.match_sessions"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
    ) -> None:
        """Test successfully matching sessions"""
        mock_session_repository.match_sessions = AsyncMock(return_value=[sample_session_data])

        action = MatchSessionsAction(
            id_or_name_prefix="test",
            owner_access_key=sample_access_key,
            user_id=sample_user_id,
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
        sample_user_id: UUID,
    ) -> None:
        """Test matching sessions when none found"""
        mock_session_repository.match_sessions = AsyncMock(return_value=[])

        action = MatchSessionsAction(
            id_or_name_prefix="nonexistent",
            owner_access_key=sample_access_key,
            user_id=sample_user_id,
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
                is_preemptible=True,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                agent_ids=[],
                domain_name="default",
                group_id=sample_group_id,
                user_uuid=sample_user_id,
                access_key=sample_access_key,
                images=["python:latest"],
                image_ids=None,
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
            user_id=sample_user_id,
        )
        result = await session_service.match_sessions(action)

        assert len(result.result) == 3
        for i, match in enumerate(result.result):
            assert match["name"] == f"test-session-{i}"


# ==================== GetStatusHistory Tests ====================


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
                force_terminated_sessions=[],
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
        assert result.session_ids == [sample_session_id]
        assert result.entity_id() == str(sample_session_id)
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
        """Test successfully destroying session (terminated status via normal termination)"""
        mock_session_repository.get_target_session_ids = AsyncMock(return_value=[sample_session_id])
        mock_scheduling_controller.mark_sessions_for_termination = AsyncMock(
            return_value=MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[sample_session_id],
                force_terminated_sessions=[],
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

        assert result.result == {"stats": {"status": "terminated"}}
        mock_scheduling_controller.mark_sessions_for_termination.assert_called_once_with(
            [sample_session_id],
            reason="user-requested",
            forced=False,
        )

    async def test_force_terminate_directly_terminated(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
    ) -> None:
        """Test force-terminate skips TERMINATING and goes directly to TERMINATED"""
        mock_session_repository.get_target_session_ids = AsyncMock(return_value=[sample_session_id])
        mock_scheduling_controller.mark_sessions_for_termination = AsyncMock(
            return_value=MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[],
                force_terminated_sessions=[sample_session_id],
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
        mock_scheduling_controller.mark_sessions_for_termination.assert_called_once_with(
            [sample_session_id],
            reason="force-terminated",
            forced=True,
        )

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
                force_terminated_sessions=[],
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
        assert result.session_ids == session_ids
        assert result.entity_id() == ",".join(str(sid) for sid in session_ids)

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
                force_terminated_sessions=[],
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
        assert result.session_ids == []
        assert result.entity_id() is None


# ==================== Complete Tests ====================


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


class TestGetSessionInfo:
    """Test cases for SessionService.get_session_info"""

    @pytest.fixture
    def mock_running_session(
        self,
        sample_session_id: SessionId,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_session_data: SessionData,
    ) -> MagicMock:
        mock_kernel = MagicMock()
        mock_kernel.image = "cr.backend.ai/stable/python:latest"
        mock_kernel.architecture = "x86_64"
        mock_kernel.registry = "cr.backend.ai"
        mock_kernel.container_id = "a" * 64
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
        return mock_session

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        mock_running_session: MagicMock,
        sample_session_data: SessionData,
        sample_access_key: AccessKey,
    ) -> None:
        """Test successfully getting session info"""
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_running_session)

        action = GetSessionInfoAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_session_info(action)

        assert isinstance(result, GetSessionInfoActionResult)
        assert result.session_info is not None
        assert result.session_info.domain_name == "default"
        assert result.session_info.image == "cr.backend.ai/stable/python:latest"
        assert result.session_info.container_id is not None
        assert result.session_info.container_id == "a" * 64
        assert result.session_data == sample_session_data
        mock_session_repository.get_session_validated.assert_called_once()

    async def test_success_with_no_container_id(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_running_session: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        """Test getting session info when container_id is None (pre-RUNNING state)"""
        mock_running_session.main_kernel.container_id = None
        mock_running_session.status = SessionStatus.PENDING
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_running_session)

        action = GetSessionInfoAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_session_info(action)

        assert isinstance(result, GetSessionInfoActionResult)
        assert result.session_info.container_id is None

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


class TestResolveSessionName:
    """Test cases for SessionService.resolve_session_name"""

    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
    ) -> None:
        """A session id resolves to its canonical session name."""
        mock_session_repository.get_session_name = AsyncMock(return_value="test-session")

        result = await session_service.resolve_session_name(
            ResolveSessionNameAction(session_id=sample_session_id)
        )

        assert isinstance(result, ResolveSessionNameActionResult)
        assert result.session_name == "test-session"
        mock_session_repository.get_session_name.assert_called_once_with(sample_session_id)

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
    ) -> None:
        """An unknown session id surfaces SessionNotFound from the repository."""
        mock_session_repository.get_session_name = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        with pytest.raises(SessionNotFound):
            await session_service.resolve_session_name(
                ResolveSessionNameAction(session_id=sample_session_id)
            )


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

        async def mock_next() -> MagicMock | None:
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
        assert cast(dict[str, Any], result.result)["result"]["logs"] == agent_logs
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


# ==================== Search Tests ====================


class TestSearch:
    """Test cases for SessionService.search"""

    async def test_search_sessions(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_data: SessionData,
        sample_user_id: UUID,
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
        action = SearchSessionsAction(querier=querier, user_id=sample_user_id)
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
        sample_user_id: UUID,
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
        action = SearchSessionsAction(querier=querier, user_id=sample_user_id)
        result = await session_service.search(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_sessions_with_pagination(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_data: SessionData,
        sample_user_id: UUID,
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
        action = SearchSessionsAction(querier=querier, user_id=sample_user_id)
        result = await session_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True


# ==================== SearchKernels Tests ====================


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
                image_id=None,
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
                resource_group_id=ResourceGroupID(uuid4()),
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
                last_observed_at=None,
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
        sample_user_id: UUID,
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
        action = SearchKernelsAction(querier=querier, user_id=sample_user_id)
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
        sample_user_id: UUID,
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
        action = SearchKernelsAction(querier=querier, user_id=sample_user_id)
        result = await session_service.search_kernels(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_kernels_with_pagination(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_kernel_info: KernelInfo,
        sample_user_id: UUID,
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
        action = SearchKernelsAction(querier=querier, user_id=sample_user_id)
        result = await session_service.search_kernels(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True


# ==================== EnqueueSession Tests ====================


class TestEnqueueSession:
    """Test cases for SessionService.enqueue_session"""

    @pytest.fixture
    def sample_image_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def picked_resource_group_id(self) -> ResourceGroupID:
        """Resource group id returned by the default auto-picker."""
        return ResourceGroupID(uuid4())

    @pytest.fixture
    def requested_resource_group_id(self) -> ResourceGroupID:
        """Resource group id supplied directly by the caller."""
        return ResourceGroupID(uuid4())

    @pytest.fixture
    def session_domain_id(self) -> DomainID:
        """Domain id resolved from the session's domain name."""
        return DomainID(uuid4())

    @pytest.fixture
    def enqueue_action_without_rg(
        self,
        sample_user_id: UUID,
        sample_access_key: AccessKey,
        sample_group_id: UUID,
        sample_image_id: UUID,
    ) -> EnqueueSessionAction:
        """Action mirroring `backend.ai session create` without `-q/--scaling-group`."""
        return EnqueueSessionAction(
            session_name="test-session",
            session_type=SessionTypes.INTERACTIVE,
            image_id=sample_image_id,
            resource=SessionResourceSpec(
                entries=[
                    ResourceSlotEntry(resource_type="cpu", quantity="1"),
                    ResourceSlotEntry(resource_type="mem", quantity="512m"),
                ],
                resource_group=None,
            ),
            scheduling=SessionSchedulingSpec(),
            user_id=sample_user_id,
            access_key=sample_access_key,
            domain_name="default",
            group_id=sample_group_id,
        )

    @pytest.fixture
    def enqueue_action_with_rg(
        self,
        enqueue_action_without_rg: EnqueueSessionAction,
    ) -> EnqueueSessionAction:
        """Same action but with the user supplying an explicit scaling group."""
        return EnqueueSessionAction(
            session_name=enqueue_action_without_rg.session_name,
            session_type=enqueue_action_without_rg.session_type,
            image_id=enqueue_action_without_rg.image_id,
            resource=SessionResourceSpec(
                entries=enqueue_action_without_rg.resource.entries,
                resource_group="requested-rg",
            ),
            scheduling=enqueue_action_without_rg.scheduling,
            user_id=enqueue_action_without_rg.user_id,
            access_key=enqueue_action_without_rg.access_key,
            domain_name=enqueue_action_without_rg.domain_name,
            group_id=enqueue_action_without_rg.group_id,
        )

    @pytest.fixture
    def configured_session_service(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
        mock_scheduler_repository: MagicMock,
        sample_session_id: SessionId,
        sample_session_data: SessionData,
        picked_resource_group_id: ResourceGroupID,
        requested_resource_group_id: ResourceGroupID,
        session_domain_id: DomainID,
    ) -> SessionService:
        """Wire async mocks every ``enqueue_session`` exercise needs."""
        mock_session_repository.resolve_image_by_id = AsyncMock()
        mock_session_repository.get_session_data_by_id = AsyncMock(return_value=sample_session_data)
        mock_scheduling_controller.enqueue_session_from_draft = AsyncMock(
            return_value=sample_session_id
        )
        mock_scheduler_repository.pick_default_resource_group = AsyncMock(
            return_value=picked_resource_group_id
        )
        rg_names = {
            picked_resource_group_id: ResourceGroupName("picked-rg"),
            requested_resource_group_id: ResourceGroupName("requested-rg"),
        }
        mock_scheduler_repository.get_resource_group_name_by_id = AsyncMock(
            side_effect=lambda resource_group_id: rg_names[resource_group_id]
        )
        mock_scheduler_repository.get_resource_group_id_by_name = AsyncMock(
            return_value=requested_resource_group_id
        )
        mock_scheduler_repository.get_domain_id_by_name = AsyncMock(return_value=session_domain_id)
        return session_service

    async def test_auto_picks_default_when_resource_group_omitted(
        self,
        configured_session_service: SessionService,
        mock_scheduler_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
        enqueue_action_without_rg: EnqueueSessionAction,
        picked_resource_group_id: ResourceGroupID,
        session_domain_id: DomainID,
    ) -> None:
        """BA-5917: when no resource group is given, the default is auto-picked
        by id and the draft carries both the id and the resolved name.
        """
        await configured_session_service.enqueue_session(enqueue_action_without_rg)

        mock_scheduler_repository.pick_default_resource_group.assert_awaited_once()
        mock_scheduler_repository.get_resource_group_name_by_id.assert_awaited_once_with(
            picked_resource_group_id
        )
        draft = mock_scheduling_controller.enqueue_session_from_draft.await_args.args[0]
        assert draft.scope.resource_group_id == picked_resource_group_id
        assert draft.scope.resource_group_name == ResourceGroupName("picked-rg")
        assert draft.scope.domain_id == session_domain_id

    async def test_uses_user_supplied_resource_group(
        self,
        configured_session_service: SessionService,
        mock_scheduler_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
        enqueue_action_with_rg: EnqueueSessionAction,
        requested_resource_group_id: ResourceGroupID,
    ) -> None:
        """When the caller supplies a scaling group name, the name is used
        as-is and only its id is resolved: no auto-picking.
        """
        await configured_session_service.enqueue_session(enqueue_action_with_rg)

        mock_scheduler_repository.pick_default_resource_group.assert_not_called()
        mock_scheduler_repository.get_resource_group_name_by_id.assert_not_called()
        mock_scheduler_repository.get_resource_group_id_by_name.assert_awaited_once_with(
            ResourceGroupName("requested-rg")
        )
        draft = mock_scheduling_controller.enqueue_session_from_draft.await_args.args[0]
        assert draft.scope.resource_group_id == requested_resource_group_id
        assert draft.scope.resource_group_name == ResourceGroupName("requested-rg")

    async def test_uses_user_supplied_resource_group_id(
        self,
        configured_session_service: SessionService,
        mock_scheduler_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
        enqueue_action_without_rg: EnqueueSessionAction,
        requested_resource_group_id: ResourceGroupID,
    ) -> None:
        """When the caller supplies a resource group id, only its name is
        looked up: no auto-picking.
        """
        action = EnqueueSessionAction(
            session_name=enqueue_action_without_rg.session_name,
            session_type=enqueue_action_without_rg.session_type,
            image_id=enqueue_action_without_rg.image_id,
            resource=SessionResourceSpec(
                entries=enqueue_action_without_rg.resource.entries,
                resource_group_id=requested_resource_group_id,
            ),
            scheduling=enqueue_action_without_rg.scheduling,
            user_id=enqueue_action_without_rg.user_id,
            access_key=enqueue_action_without_rg.access_key,
            domain_name=enqueue_action_without_rg.domain_name,
            group_id=enqueue_action_without_rg.group_id,
        )

        await configured_session_service.enqueue_session(action)

        mock_scheduler_repository.pick_default_resource_group.assert_not_called()
        mock_scheduler_repository.get_resource_group_id_by_name.assert_not_called()
        mock_scheduler_repository.get_resource_group_name_by_id.assert_awaited_once_with(
            requested_resource_group_id
        )
        draft = mock_scheduling_controller.enqueue_session_from_draft.await_args.args[0]
        assert draft.scope.resource_group_id == requested_resource_group_id
        assert draft.scope.resource_group_name == ResourceGroupName("requested-rg")
