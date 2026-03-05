"""
Unit tests for SessionService lifecycle actions.
Tests the service layer with mocked repositories.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.exception import InvalidAPIParameters, UnknownImageReference
from ai.backend.common.types import (
    AbuseReport,
    AccessKey,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.api.utils import undefined
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.errors.common import ServiceUnavailable
from ai.backend.manager.errors.image import UnknownImageReferenceError
from ai.backend.manager.errors.kernel import (
    InvalidSessionData,
    KernelNotReady,
    QuotaExceeded,
    SessionAlreadyExists,
    SessionNotFound,
    TooManySessionsMatched,
)
from ai.backend.manager.errors.resource import AppNotFound, TaskTemplateNotFound
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.session.actions.check_and_transit_status import (
    CheckAndTransitStatusBatchAction,
)
from ai.backend.manager.services.session.actions.commit_session import (
    CommitSessionAction,
)
from ai.backend.manager.services.session.actions.create_cluster import (
    CreateClusterAction,
)
from ai.backend.manager.services.session.actions.create_from_params import (
    CreateFromParamsAction,
    CreateFromParamsActionParams,
)
from ai.backend.manager.services.session.actions.create_from_template import (
    CreateFromTemplateAction,
    CreateFromTemplateActionParams,
)
from ai.backend.manager.services.session.actions.execute_session import (
    ExecuteSessionAction,
    ExecuteSessionActionParams,
)
from ai.backend.manager.services.session.actions.get_abusing_report import (
    GetAbusingReportAction,
)
from ai.backend.manager.services.session.actions.get_commit_status import (
    GetCommitStatusAction,
)
from ai.backend.manager.services.session.actions.get_dependency_graph import (
    GetDependencyGraphAction,
)
from ai.backend.manager.services.session.actions.get_direct_access_info import (
    GetDirectAccessInfoAction,
)
from ai.backend.manager.services.session.actions.match_sessions import (
    MatchSessionsAction,
)
from ai.backend.manager.services.session.actions.shutdown_service import (
    ShutdownServiceAction,
)
from ai.backend.manager.services.session.actions.start_service import (
    StartServiceAction,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs

# ==================== Shared Fixtures ====================


@pytest.fixture
def mock_session_repository() -> MagicMock:
    return MagicMock(spec=SessionRepository)


@pytest.fixture
def mock_agent_registry() -> MagicMock:
    mock = MagicMock()
    mock.increment_session_usage = AsyncMock()
    mock.session_lifecycle_mgr = MagicMock()
    mock.session_lifecycle_mgr.transit_session_status = AsyncMock(return_value=[])
    mock.session_lifecycle_mgr.deregister_status_updatable_session = AsyncMock()
    return mock


@pytest.fixture
def mock_event_fetcher() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_background_task_manager() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_event_hub() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_error_monitor() -> MagicMock:
    mock = MagicMock()
    mock.capture_exception = AsyncMock()
    return mock


@pytest.fixture
def mock_idle_checker_host() -> MagicMock:
    mock = MagicMock()
    mock.get_idle_check_report = AsyncMock(return_value={})
    return mock


@pytest.fixture
def mock_scheduling_controller() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_appproxy_client_pool() -> MagicMock:
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
    mock_appproxy_client_pool: MagicMock,
) -> SessionService:
    args = SessionServiceArgs(
        agent_registry=mock_agent_registry,
        event_fetcher=mock_event_fetcher,
        background_task_manager=mock_background_task_manager,
        event_hub=mock_event_hub,
        error_monitor=mock_error_monitor,
        idle_checker_host=mock_idle_checker_host,
        session_repository=mock_session_repository,
        scheduling_controller=mock_scheduling_controller,
        appproxy_client_pool=mock_appproxy_client_pool,
    )
    return SessionService(args)


@pytest.fixture
def sample_session_id() -> SessionId:
    return SessionId(uuid4())


@pytest.fixture
def sample_access_key() -> AccessKey:
    return AccessKey("AKIAIOSFODNN7EXAMPLE")


@pytest.fixture
def sample_user_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_group_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_kernel_id() -> KernelId:
    return KernelId(uuid4())


def _make_session_data(
    session_id: SessionId,
    access_key: AccessKey,
    user_id: UUID,
    group_id: UUID,
    *,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
    status: SessionStatus = SessionStatus.RUNNING,
    name: str = "test-session",
) -> SessionData:
    return SessionData(
        id=session_id,
        creation_id="test-creation-id",
        name=name,
        session_type=session_type,
        priority=0,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        agent_ids=["i-ubuntu"],
        domain_name="default",
        group_id=group_id,
        user_uuid=user_id,
        access_key=access_key,
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
        status=status,
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


def _make_mock_session(
    session_id: SessionId,
    access_key: AccessKey,
    user_id: UUID,
    group_id: UUID,
    kernel_id: KernelId,
    *,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
) -> MagicMock:
    """Create a mock session row with main_kernel."""
    session = MagicMock()
    session.id = session_id
    session.session_type = session_type
    session.user_uuid = user_id
    session.group_id = group_id
    session.access_key = access_key
    session.domain_name = "default"
    session.scaling_group_name = "default"
    session.main_kernel = MagicMock()
    session.main_kernel.id = kernel_id
    session.main_kernel.status = MagicMock()
    session.main_kernel.status.name = "RUNNING"
    session.main_kernel.agent_row = MagicMock()
    session.main_kernel.agent_row.public_host = "10.0.0.1"
    session.main_kernel.agent_addr = "tcp://10.0.0.1:6001"
    session.main_kernel.kernel_host = "10.0.0.1"
    session.main_kernel.service_ports = [
        {"name": "sshd", "host_ports": [2200], "container_ports": [22]},
        {"name": "sftpd", "host_ports": [2201], "container_ports": [115]},
    ]
    session.to_dataclass.return_value = _make_session_data(
        session_id, access_key, user_id, group_id, session_type=session_type
    )
    return session


# ==================== CommitSession Tests ====================


class TestCommitSession:
    async def test_commit_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.commit_session_to_file = AsyncMock(return_value={"taskId": "task-123"})

        action = CommitSessionAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
            filename=None,
        )

        with patch("asyncio.current_task", return_value=MagicMock()):
            result = await session_service.commit_session(action)

        assert result.commit_result == {"taskId": "task-123"}
        mock_session_repository.get_session_validated.assert_called_once()

    async def test_commit_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = CommitSessionAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
            filename=None,
        )

        with (
            patch("asyncio.current_task", return_value=MagicMock()),
            pytest.raises(SessionNotFound),
        ):
            await session_service.commit_session(action)

    async def test_commit_custom_filename(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.commit_session_to_file = AsyncMock(return_value={"taskId": "task-456"})

        action = CommitSessionAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
            filename="my-snapshot.tar.gz",
        )

        with patch("asyncio.current_task", return_value=MagicMock()):
            await session_service.commit_session(action)

        # Verify filename was passed through
        call_args = mock_agent_registry.commit_session_to_file.call_args
        assert call_args[0][1] == "my-snapshot.tar.gz"


# ==================== GetCommitStatus Tests ====================


class TestGetCommitStatus:
    async def test_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.get_commit_status = AsyncMock(return_value={sample_kernel_id: "clean"})

        action = GetCommitStatusAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_commit_status(action)

        assert result.commit_info.status == "clean"
        assert result.commit_info.kernel == str(sample_kernel_id)

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("Session not found")
        )

        action = GetCommitStatusAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(SessionNotFound):
            await session_service.get_commit_status(action)


# ==================== ExecuteSession Tests ====================


class TestExecuteSession:
    async def test_v1_query_mode(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.execute = AsyncMock(
            return_value={
                "status": "finished",
                "runId": "auto-run-id",
                "exitCode": 0,
                "stdout": "hello",
                "stderr": "",
                "options": None,
                "files": None,
                "media": None,
                "html": None,
            }
        )

        action = ExecuteSessionAction(
            session_name="test-session",
            api_version=(1,),
            owner_access_key=sample_access_key,
            params=ExecuteSessionActionParams(
                mode=None,
                options=None,
                code='print("hello")',
                run_id=None,
            ),
        )
        result = await session_service.execute_session(action)

        assert "result" in result.result
        assert result.result["result"]["stdout"] == "hello"
        # V1 auto-generates run_id
        call_args = mock_agent_registry.execute.call_args
        assert call_args[0][2] is not None  # run_id generated

    async def test_v2_batch_mode(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.execute = AsyncMock(
            return_value={
                "status": "finished",
                "runId": "my-run-id",
                "exitCode": 0,
                "options": None,
                "files": None,
                "console": [],
            }
        )

        action = ExecuteSessionAction(
            session_name="test-session",
            api_version=(2,),
            owner_access_key=sample_access_key,
            params=ExecuteSessionActionParams(
                mode="batch",
                options=None,
                code='print("hello")',
                run_id="my-run-id",
            ),
        )
        result = await session_service.execute_session(action)

        assert result.result["result"]["exitCode"] == 0
        assert "console" in result.result["result"]
        assert "stdout" not in result.result["result"]

    async def test_v2_complete_mode(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        mock_completion = MagicMock()
        mock_completion.as_dict.return_value = {
            "candidates": ["print", "println"],
        }
        mock_agent_registry.get_completions = AsyncMock(return_value=mock_completion)

        action = ExecuteSessionAction(
            session_name="test-session",
            api_version=(2,),
            owner_access_key=sample_access_key,
            params=ExecuteSessionActionParams(
                mode="complete",
                options={},
                code="pri",
                run_id=None,
            ),
        )
        result = await session_service.execute_session(action)

        assert "candidates" in result.result["result"]

    async def test_v2_continue_without_run_id_raises(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = ExecuteSessionAction(
            session_name="test-session",
            api_version=(2,),
            owner_access_key=sample_access_key,
            params=ExecuteSessionActionParams(
                mode="continue",
                options=None,
                code="",
                run_id=None,
            ),
        )

        with pytest.raises(InvalidSessionData):
            await session_service.execute_session(action)

    async def test_v2_invalid_mode_raises(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = ExecuteSessionAction(
            session_name="test-session",
            api_version=(2,),
            owner_access_key=sample_access_key,
            params=ExecuteSessionActionParams(
                mode="invalid_mode",
                options=None,
                code="",
                run_id=None,
            ),
        )

        with pytest.raises(InvalidSessionData):
            await session_service.execute_session(action)

    async def test_v2_null_mode_raises(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = ExecuteSessionAction(
            session_name="test-session",
            api_version=(2,),
            owner_access_key=sample_access_key,
            params=ExecuteSessionActionParams(
                mode=None,
                options=None,
                code="x = 1",
                run_id=None,
            ),
        )

        with pytest.raises(InvalidSessionData):
            await session_service.execute_session(action)

    async def test_null_code_defaults_to_empty_string(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.execute = AsyncMock(
            return_value={
                "status": "finished",
                "runId": "test-run",
                "exitCode": 0,
                "options": None,
                "files": None,
                "console": [],
            }
        )

        action = ExecuteSessionAction(
            session_name="test-session",
            api_version=(2,),
            owner_access_key=sample_access_key,
            params=ExecuteSessionActionParams(
                mode="query",
                options=None,
                code=None,
                run_id="test-run",
            ),
        )
        await session_service.execute_session(action)

        call_args = mock_agent_registry.execute.call_args
        assert call_args[0][4] == ""  # code
        assert call_args[0][5] == {}  # opts


# ==================== CreateFromParams Tests ====================


class TestCreateFromParams:
    async def test_image_resolve_failure_raises(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
    ) -> None:
        mock_session_repository.query_userinfo = AsyncMock(
            return_value=(sample_user_id, sample_group_id, {})
        )
        mock_session_repository.resolve_image = AsyncMock(
            side_effect=UnknownImageReference("unknown image")
        )

        action = CreateFromParamsAction(
            params=CreateFromParamsActionParams(
                session_name="test-session",
                image="nonexistent:latest",
                architecture="x86_64",
                session_type=SessionTypes.INTERACTIVE,
                group_name="default",
                domain_name="default",
                cluster_size=1,
                cluster_mode=ClusterMode.SINGLE_NODE,
                config={},
                tag="",
                priority=0,
                owner_access_key=sample_access_key,
                enqueue_only=False,
                max_wait_seconds=0,
                starts_at=None,
                reuse_if_exists=False,
                startup_command=None,
                batch_timeout=None,
                bootstrap_script=None,
                dependencies=None,
                callback_url=None,
            ),
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            requester_access_key=sample_access_key,
            keypair_resource_policy=None,
        )

        with pytest.raises(UnknownImageReferenceError):
            await session_service.create_from_params(action)

    async def test_invalid_domain_group_raises(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
    ) -> None:
        mock_session_repository.query_userinfo = AsyncMock(
            side_effect=ValueError("Invalid domain/group combination")
        )

        action = CreateFromParamsAction(
            params=CreateFromParamsActionParams(
                session_name="test-session",
                image="python:latest",
                architecture="x86_64",
                session_type=SessionTypes.INTERACTIVE,
                group_name="bad-group",
                domain_name="bad-domain",
                cluster_size=1,
                cluster_mode=ClusterMode.SINGLE_NODE,
                config={},
                tag="",
                priority=0,
                owner_access_key=sample_access_key,
                enqueue_only=False,
                max_wait_seconds=0,
                starts_at=None,
                reuse_if_exists=False,
                startup_command=None,
                batch_timeout=None,
                bootstrap_script=None,
                dependencies=None,
                callback_url=None,
            ),
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            requester_access_key=sample_access_key,
            keypair_resource_policy=None,
        )

        with pytest.raises(ValueError):
            await session_service.create_from_params(action)

    async def test_create_distributed_session(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
    ) -> None:
        new_session_id = str(uuid4())
        mock_session_repository.query_userinfo = AsyncMock(
            return_value=(sample_user_id, sample_group_id, {})
        )
        mock_image_row = MagicMock()
        mock_image_row.image_ref = MagicMock()
        mock_session_repository.resolve_image = AsyncMock(return_value=mock_image_row)
        mock_agent_registry.create_session = AsyncMock(return_value={"sessionId": new_session_id})

        action = CreateFromParamsAction(
            params=CreateFromParamsActionParams(
                session_name="distributed-session",
                image="python:latest",
                architecture="x86_64",
                session_type=SessionTypes.INTERACTIVE,
                group_name="default",
                domain_name="default",
                cluster_size=3,
                cluster_mode=ClusterMode.MULTI_NODE,
                config={},
                tag="",
                priority=0,
                owner_access_key=sample_access_key,
                enqueue_only=False,
                max_wait_seconds=0,
                starts_at=None,
                reuse_if_exists=False,
                startup_command=None,
                batch_timeout=None,
                bootstrap_script=None,
                dependencies=None,
                callback_url=None,
            ),
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            requester_access_key=sample_access_key,
            keypair_resource_policy=None,
        )

        result = await session_service.create_from_params(action)
        assert result.session_id == uuid.UUID(new_session_id)

        # Verify create_session was called (cluster_size passed as positional arg)
        mock_agent_registry.create_session.assert_called_once()

    async def test_reuse_if_exists_returns_existing(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
    ) -> None:
        existing_session_id = str(uuid4())
        mock_session_repository.query_userinfo = AsyncMock(
            return_value=(sample_user_id, sample_group_id, {})
        )
        mock_image_row = MagicMock()
        mock_image_row.image_ref = MagicMock()
        mock_session_repository.resolve_image = AsyncMock(return_value=mock_image_row)
        mock_agent_registry.create_session = AsyncMock(
            return_value={"sessionId": existing_session_id, "created": False}
        )

        action = CreateFromParamsAction(
            params=CreateFromParamsActionParams(
                session_name="existing-session",
                image="python:latest",
                architecture="x86_64",
                session_type=SessionTypes.INTERACTIVE,
                group_name="default",
                domain_name="default",
                cluster_size=1,
                cluster_mode=ClusterMode.SINGLE_NODE,
                config={},
                tag="",
                priority=0,
                owner_access_key=sample_access_key,
                enqueue_only=False,
                max_wait_seconds=0,
                starts_at=None,
                reuse_if_exists=True,
                startup_command=None,
                batch_timeout=None,
                bootstrap_script=None,
                dependencies=None,
                callback_url=None,
            ),
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            requester_access_key=sample_access_key,
            keypair_resource_policy=None,
        )

        result = await session_service.create_from_params(action)
        assert result.session_id == uuid.UUID(existing_session_id)
        # Verify reuse flag was passed
        call_kwargs = mock_agent_registry.create_session.call_args[1]
        assert call_kwargs["reuse"] is True

    async def test_quota_exceeded_raises(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
    ) -> None:
        mock_session_repository.query_userinfo = AsyncMock(
            return_value=(sample_user_id, sample_group_id, {})
        )
        mock_image_row = MagicMock()
        mock_image_row.image_ref = MagicMock()
        mock_session_repository.resolve_image = AsyncMock(return_value=mock_image_row)
        mock_agent_registry.create_session = AsyncMock(side_effect=QuotaExceeded("Quota exceeded"))

        action = CreateFromParamsAction(
            params=CreateFromParamsActionParams(
                session_name="test-session",
                image="python:latest",
                architecture="x86_64",
                session_type=SessionTypes.INTERACTIVE,
                group_name="default",
                domain_name="default",
                cluster_size=1,
                cluster_mode=ClusterMode.SINGLE_NODE,
                config={},
                tag="",
                priority=0,
                owner_access_key=sample_access_key,
                enqueue_only=False,
                max_wait_seconds=0,
                starts_at=None,
                reuse_if_exists=False,
                startup_command=None,
                batch_timeout=None,
                bootstrap_script=None,
                dependencies=None,
                callback_url=None,
            ),
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            requester_access_key=sample_access_key,
            keypair_resource_policy=None,
        )

        with pytest.raises(QuotaExceeded):
            await session_service.create_from_params(action)


# ==================== CreateFromTemplate Tests ====================


class TestCreateFromTemplate:
    @pytest.fixture
    def sample_template(self) -> dict[str, Any]:
        return {
            "metadata": {"tag": "test-tag"},
            "spec": {
                "kernel": {
                    "image": "python:latest",
                    "architecture": "x86_64",
                    "run": {
                        "bootstrap": None,
                        "startup_command": None,
                    },
                    "git": None,
                    "environ": {},
                },
                "session_type": "interactive",
                "scaling_group": None,
                "mounts": None,
                "resources": None,
            },
        }

    async def test_create_from_template_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_template: dict[str, Any],
    ) -> None:
        template_id = uuid4()
        new_session_id = str(uuid4())
        mock_session_repository.get_template_info_by_id = AsyncMock(
            return_value={
                "template": sample_template,
                "domain_name": "default",
                "group_id": sample_group_id,
            }
        )
        mock_session_repository.get_group_name_by_domain_and_id = AsyncMock(return_value="default")
        mock_session_repository.query_userinfo = AsyncMock(
            return_value=(sample_user_id, sample_group_id, {})
        )
        mock_image_row = MagicMock()
        mock_image_row.image_ref = MagicMock()
        mock_session_repository.resolve_image = AsyncMock(return_value=mock_image_row)
        mock_agent_registry.create_session = AsyncMock(return_value={"sessionId": new_session_id})

        action = CreateFromTemplateAction(
            params=CreateFromTemplateActionParams(
                template_id=template_id,
                session_name="template-session",
                image=undefined,
                architecture=undefined,
                session_type=undefined,
                group_name="default",
                domain_name="default",
                cluster_size=1,
                cluster_mode=ClusterMode.SINGLE_NODE,
                config={},
                tag=undefined,
                priority=0,
                owner_access_key=sample_access_key,
                enqueue_only=False,
                max_wait_seconds=0,
                starts_at=None,
                reuse_if_exists=False,
                startup_command=None,
                batch_timeout=None,
                bootstrap_script=undefined,
                dependencies=None,
                callback_url=None,
            ),
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            requester_access_key=sample_access_key,
            keypair_resource_policy=None,
        )

        result = await session_service.create_from_template(action)
        assert result.session_id == new_session_id

    async def test_template_not_found_raises(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
    ) -> None:
        template_id = uuid4()
        mock_session_repository.get_template_info_by_id = AsyncMock(return_value=None)

        action = CreateFromTemplateAction(
            params=CreateFromTemplateActionParams(
                template_id=template_id,
                session_name="template-session",
                image="python:latest",
                architecture="x86_64",
                session_type=SessionTypes.INTERACTIVE,
                group_name="default",
                domain_name="default",
                cluster_size=1,
                cluster_mode=ClusterMode.SINGLE_NODE,
                config={},
                tag="",
                priority=0,
                owner_access_key=sample_access_key,
                enqueue_only=False,
                max_wait_seconds=0,
                starts_at=None,
                reuse_if_exists=False,
                startup_command=None,
                batch_timeout=None,
                bootstrap_script=None,
                dependencies=None,
                callback_url=None,
            ),
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            requester_access_key=sample_access_key,
            keypair_resource_policy=None,
        )

        with pytest.raises(TaskTemplateNotFound):
            await session_service.create_from_template(action)


# ==================== CreateCluster Tests ====================


class TestCreateCluster:
    async def test_create_cluster_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
    ) -> None:
        template_id = uuid4()
        kernel_id = str(uuid4())
        mock_session_repository.get_template_by_id = AsyncMock(
            return_value={"template": "some-template"}
        )
        mock_session_repository.query_userinfo = AsyncMock(
            return_value=(sample_user_id, sample_group_id, {})
        )
        mock_agent_registry.create_cluster = AsyncMock(return_value={"kernelId": kernel_id})

        action = CreateClusterAction(
            session_name="cluster-session",
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            template_id=template_id,
            session_type=SessionTypes.INTERACTIVE,
            group_name="default",
            domain_name="default",
            scaling_group_name="default",
            requester_access_key=sample_access_key,
            owner_access_key=sample_access_key,
            tag="",
            enqueue_only=False,
            keypair_resource_policy=None,
            max_wait_seconds=0,
        )

        result = await session_service.create_cluster(action)
        assert result.session_id == kernel_id

    async def test_template_not_found_raises(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
    ) -> None:
        template_id = uuid4()
        mock_session_repository.get_template_by_id = AsyncMock(return_value=None)

        action = CreateClusterAction(
            session_name="cluster-session",
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            template_id=template_id,
            session_type=SessionTypes.INTERACTIVE,
            group_name="default",
            domain_name="default",
            scaling_group_name="default",
            requester_access_key=sample_access_key,
            owner_access_key=sample_access_key,
            tag="",
            enqueue_only=False,
            keypair_resource_policy=None,
            max_wait_seconds=0,
        )

        with pytest.raises(TaskTemplateNotFound):
            await session_service.create_cluster(action)

    async def test_too_many_sessions_converts_to_already_exists(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
    ) -> None:
        template_id = uuid4()
        mock_session_repository.get_template_by_id = AsyncMock(
            return_value={"template": "some-template"}
        )
        mock_session_repository.query_userinfo = AsyncMock(
            return_value=(sample_user_id, sample_group_id, {})
        )
        mock_agent_registry.create_cluster = AsyncMock(
            side_effect=TooManySessionsMatched("too many")
        )

        action = CreateClusterAction(
            session_name="cluster-session",
            user_id=sample_user_id,
            user_role=UserRole.USER,
            sudo_session_enabled=False,
            template_id=template_id,
            session_type=SessionTypes.INTERACTIVE,
            group_name="default",
            domain_name="default",
            scaling_group_name="default",
            requester_access_key=sample_access_key,
            owner_access_key=sample_access_key,
            tag="",
            enqueue_only=False,
            keypair_resource_policy=None,
            max_wait_seconds=0,
        )

        with pytest.raises(SessionAlreadyExists):
            await session_service.create_cluster(action)


# ==================== MatchSessions Tests ====================


class TestMatchSessions:
    async def test_prefix_matching_returns_sessions(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
    ) -> None:
        mock_session_data = _make_session_data(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id
        )
        mock_session_repository.match_sessions = AsyncMock(return_value=[mock_session_data])

        # Need to use a mock that has .id, .name, .status attributes
        mock_match = MagicMock()
        mock_match.id = sample_session_id
        mock_match.name = "test-session"
        mock_match.status = SessionStatus.RUNNING
        mock_session_repository.match_sessions = AsyncMock(return_value=[mock_match])

        action = MatchSessionsAction(
            id_or_name_prefix="test",
            owner_access_key=sample_access_key,
        )
        result = await session_service.match_sessions(action)

        assert len(result.result) == 1
        assert result.result[0]["id"] == str(sample_session_id)
        assert result.result[0]["name"] == "test-session"

    async def test_no_match_returns_empty(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        mock_session_repository.match_sessions = AsyncMock(return_value=[])

        action = MatchSessionsAction(
            id_or_name_prefix="nonexistent",
            owner_access_key=sample_access_key,
        )
        result = await session_service.match_sessions(action)

        assert result.result == []

    async def test_owner_access_key_filtering(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        mock_session_repository.match_sessions = AsyncMock(return_value=[])

        action = MatchSessionsAction(
            id_or_name_prefix="test",
            owner_access_key=sample_access_key,
        )
        await session_service.match_sessions(action)

        mock_session_repository.match_sessions.assert_called_once_with("test", sample_access_key)


# ==================== GetAbusingReport Tests ====================


class TestGetAbusingReport:
    async def test_valid_session_returns_report(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_report: AbuseReport = {"kernel": str(sample_kernel_id), "abuse_report": "detected"}
        mock_agent_registry.get_abusing_report = AsyncMock(return_value=mock_report)

        action = GetAbusingReportAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_abusing_report(action)

        assert result.abuse_report == mock_report

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("not found")
        )

        action = GetAbusingReportAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(SessionNotFound):
            await session_service.get_abusing_report(action)


# ==================== GetDirectAccessInfo Tests ====================


class TestGetDirectAccessInfo:
    async def test_system_session_returns_ports(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        """SYSTEM type sessions (PRIVATE_SESSION_TYPES) return sshd/sftpd ports."""
        mock_session = _make_mock_session(
            sample_session_id,
            sample_access_key,
            sample_user_id,
            sample_group_id,
            sample_kernel_id,
            session_type=SessionTypes.SYSTEM,
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = GetDirectAccessInfoAction(
            session_name="system-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_direct_access_info(action)

        assert "sshd_ports" in result.result
        assert result.result["public_host"] == "10.0.0.1"

    async def test_interactive_session_returns_empty_dict(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        """Non-SYSTEM sessions (INTERACTIVE, BATCH, INFERENCE) return empty dict."""
        mock_session = _make_mock_session(
            sample_session_id,
            sample_access_key,
            sample_user_id,
            sample_group_id,
            sample_kernel_id,
            session_type=SessionTypes.INTERACTIVE,
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = GetDirectAccessInfoAction(
            session_name="interactive-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_direct_access_info(action)

        assert result.result == {}

    async def test_agent_row_none_raises_kernel_not_ready(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id,
            sample_access_key,
            sample_user_id,
            sample_group_id,
            sample_kernel_id,
            session_type=SessionTypes.SYSTEM,
        )
        mock_session.main_kernel.agent_row = None
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)

        action = GetDirectAccessInfoAction(
            session_name="system-session",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(KernelNotReady):
            await session_service.get_direct_access_info(action)


# ==================== GetDependencyGraph Tests ====================


class TestGetDependencyGraph:
    async def test_session_with_dependencies(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        dep_graph: dict[str, Any] = {
            "session_id": str(sample_session_id),
            "children": [
                {"session_id": str(uuid4()), "children": []},
            ],
        }
        mock_session_repository.find_dependency_sessions = AsyncMock(return_value=dep_graph)
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_by_id = AsyncMock(return_value=mock_session)

        action = GetDependencyGraphAction(
            root_session_name="root-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_dependency_graph(action)

        assert result.result == dep_graph
        assert "children" in result.result

    async def test_root_only_session(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        dep_graph: dict[str, Any] = {
            "session_id": str(sample_session_id),
            "children": [],
        }
        mock_session_repository.find_dependency_sessions = AsyncMock(return_value=dep_graph)
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_by_id = AsyncMock(return_value=mock_session)

        action = GetDependencyGraphAction(
            root_session_name="root-session",
            owner_access_key=sample_access_key,
        )
        result = await session_service.get_dependency_graph(action)

        assert result.result["children"] == []

    async def test_empty_session_id_raises_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        dep_graph: dict[str, Any] = {"session_id": "", "children": []}
        mock_session_repository.find_dependency_sessions = AsyncMock(return_value=dep_graph)
        mock_session_repository.get_session_by_id = AsyncMock(return_value=None)

        action = GetDependencyGraphAction(
            root_session_name="root-session",
            owner_access_key=sample_access_key,
        )

        with pytest.raises(SessionNotFound):
            await session_service.get_dependency_graph(action)


# ==================== StartService Tests ====================


class TestStartService:
    async def test_valid_service_returns_token(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        mock_appproxy_client_pool: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session.main_kernel.service_ports = [
            {
                "name": "jupyter",
                "host_ports": [8888],
                "container_ports": [8888],
                "is_inference": False,
            },
        ]
        mock_session_repository.get_session_with_routing_minimal = AsyncMock(
            return_value=mock_session
        )
        mock_session_repository.get_scaling_group_wsproxy_addr = AsyncMock(
            return_value="http://wsproxy:10200"
        )

        mock_client = MagicMock()
        mock_status = MagicMock()
        mock_status.advertise_address = "ws://wsproxy-public:10200"
        mock_client.fetch_status = AsyncMock(return_value=mock_status)
        mock_appproxy_client_pool.load_client.return_value = mock_client

        mock_agent_registry.start_service = AsyncMock(return_value={"status": "started"})

        mock_resp = MagicMock()
        mock_resp.json = AsyncMock(return_value={"token": "test-token-xyz"})

        action = StartServiceAction(
            session_name="test-session",
            access_key=sample_access_key,
            service="jupyter",
            login_session_token="login-token",
            port=None,
            arguments=None,
            envs=None,
        )

        with patch("aiohttp.ClientSession") as mock_aiohttp:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_ctx.post.return_value = MagicMock()
            mock_ctx.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_ctx.post.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_aiohttp.return_value = mock_ctx

            result = await session_service.start_service(action)

        assert result.token == "test-token-xyz"
        assert result.wsproxy_addr == "ws://wsproxy-public:10200"

    async def test_invalid_service_name_raises_app_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_appproxy_client_pool: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session.main_kernel.service_ports = [
            {
                "name": "jupyter",
                "host_ports": [8888],
                "container_ports": [8888],
                "is_inference": False,
            },
        ]
        mock_session_repository.get_session_with_routing_minimal = AsyncMock(
            return_value=mock_session
        )
        mock_session_repository.get_scaling_group_wsproxy_addr = AsyncMock(
            return_value="http://wsproxy:10200"
        )

        mock_client = MagicMock()
        mock_status = MagicMock()
        mock_status.advertise_address = None
        mock_client.fetch_status = AsyncMock(return_value=mock_status)
        mock_appproxy_client_pool.load_client.return_value = mock_client

        action = StartServiceAction(
            session_name="test-session",
            access_key=sample_access_key,
            service="nonexistent-service",
            login_session_token="login-token",
            port=None,
            arguments=None,
            envs=None,
        )

        with pytest.raises(AppNotFound):
            await session_service.start_service(action)

    async def test_no_scaling_group_raises_service_unavailable(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session.scaling_group_name = None
        mock_session_repository.get_session_with_routing_minimal = AsyncMock(
            return_value=mock_session
        )

        action = StartServiceAction(
            session_name="test-session",
            access_key=sample_access_key,
            service="jupyter",
            login_session_token="login-token",
            port=None,
            arguments=None,
            envs=None,
        )

        with pytest.raises(ServiceUnavailable):
            await session_service.start_service(action)

    async def test_inference_app_raises_invalid_api_parameters(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_appproxy_client_pool: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session.main_kernel.service_ports = [
            {
                "name": "inference-app",
                "host_ports": [8080],
                "container_ports": [8080],
                "is_inference": True,
            },
        ]
        mock_session_repository.get_session_with_routing_minimal = AsyncMock(
            return_value=mock_session
        )
        mock_session_repository.get_scaling_group_wsproxy_addr = AsyncMock(
            return_value="http://wsproxy:10200"
        )

        mock_client = MagicMock()
        mock_status = MagicMock()
        mock_status.advertise_address = None
        mock_client.fetch_status = AsyncMock(return_value=mock_status)
        mock_appproxy_client_pool.load_client.return_value = mock_client

        action = StartServiceAction(
            session_name="test-session",
            access_key=sample_access_key,
            service="inference-app",
            login_session_token="login-token",
            port=None,
            arguments=None,
            envs=None,
        )

        with pytest.raises(InvalidAPIParameters):
            await session_service.start_service(action)


# ==================== ShutdownService Tests ====================


class TestShutdownService:
    async def test_shutdown_success(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_session_id: SessionId,
        sample_access_key: AccessKey,
        sample_user_id: UUID,
        sample_group_id: UUID,
        sample_kernel_id: KernelId,
    ) -> None:
        mock_session = _make_mock_session(
            sample_session_id, sample_access_key, sample_user_id, sample_group_id, sample_kernel_id
        )
        mock_session_repository.get_session_validated = AsyncMock(return_value=mock_session)
        mock_agent_registry.shutdown_service = AsyncMock()

        action = ShutdownServiceAction(
            session_name="test-session",
            owner_access_key=sample_access_key,
            service_name="jupyter",
        )
        result = await session_service.shutdown_service(action)

        assert result.result is None
        mock_agent_registry.shutdown_service.assert_called_once_with(mock_session, "jupyter")

    async def test_session_not_found(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        sample_access_key: AccessKey,
    ) -> None:
        mock_session_repository.get_session_validated = AsyncMock(
            side_effect=SessionNotFound("not found")
        )

        action = ShutdownServiceAction(
            session_name="nonexistent",
            owner_access_key=sample_access_key,
            service_name="jupyter",
        )

        with pytest.raises(SessionNotFound):
            await session_service.shutdown_service(action)


# ==================== CheckAndTransitStatusBatch Tests ====================


class _TestCheckAndTransitStatusBatchAction(CheckAndTransitStatusBatchAction):
    """Concrete subclass for testing (field_data is abstract in BaseBatchAction)."""

    def field_data(self) -> None:
        return None


class TestCheckAndTransitStatusBatch:
    async def test_admin_processes_all_sessions(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_user_id: UUID,
    ) -> None:
        sid1 = SessionId(uuid4())
        sid2 = SessionId(uuid4())

        mock_row1 = MagicMock()
        mock_row1.id = sid1
        mock_row1.status = SessionStatus.RUNNING
        mock_row2 = MagicMock()
        mock_row2.id = sid2
        mock_row2.status = SessionStatus.RUNNING

        mock_agent_registry.session_lifecycle_mgr.transit_session_status = AsyncMock(
            return_value=[(mock_row1, True), (mock_row2, True)]
        )

        action = _TestCheckAndTransitStatusBatchAction(
            user_id=sample_user_id,
            user_role=UserRole.ADMIN,
            session_ids=[sid1, sid2],
        )
        result = await session_service.check_and_transit_status_multi(action)

        assert sid1 in result.session_status_map
        assert sid2 in result.session_status_map

    async def test_user_role_only_processes_owned_sessions(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_user_id: UUID,
    ) -> None:
        owned_sid = SessionId(uuid4())
        other_sid = SessionId(uuid4())
        other_user_id = uuid4()

        owned_session_row = MagicMock()
        owned_session_row.user_uuid = sample_user_id
        other_session_row = MagicMock()
        other_session_row.user_uuid = other_user_id

        mock_session_repository.get_session_to_determine_status = AsyncMock(
            side_effect=lambda sid: owned_session_row if sid == owned_sid else other_session_row
        )

        mock_row = MagicMock()
        mock_row.id = owned_sid
        mock_row.status = SessionStatus.RUNNING

        mock_agent_registry.session_lifecycle_mgr.transit_session_status = AsyncMock(
            return_value=[(mock_row, True)]
        )

        action = _TestCheckAndTransitStatusBatchAction(
            user_id=sample_user_id,
            user_role=UserRole.USER,
            session_ids=[owned_sid, other_sid],
        )
        result = await session_service.check_and_transit_status_multi(action)

        assert owned_sid in result.session_status_map
        assert other_sid not in result.session_status_map

    async def test_empty_session_ids_returns_empty(
        self,
        session_service: SessionService,
        mock_session_repository: MagicMock,
        mock_agent_registry: MagicMock,
        sample_user_id: UUID,
    ) -> None:
        action = _TestCheckAndTransitStatusBatchAction(
            user_id=sample_user_id,
            user_role=UserRole.USER,
            session_ids=[],
        )
        result = await session_service.check_and_transit_status_multi(action)

        assert result.session_status_map == {}
