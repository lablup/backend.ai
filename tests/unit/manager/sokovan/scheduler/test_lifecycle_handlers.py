"""
Tests for SessionLifecycleHandler implementations.

Tests the new lifecycle handler pattern following DeploymentCoordinator style.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import (
    AccessKey,
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
from ai.backend.manager.data.session.types import (
    ImageSpec,
    MountSpec,
    ResourceSpec,
    SessionExecution,
    SessionIdentity,
    SessionInfo,
    SessionLifecycle,
    SessionMetadata,
    SessionMetrics,
    SessionNetwork,
    SessionStatus,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.scheduler.handlers import (
    CheckCreatingProgressLifecycleHandler,
    CheckPullingProgressLifecycleHandler,
    CheckRunningSessionTerminationLifecycleHandler,
    CheckTerminatingProgressLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.results import (
    ScheduledSessionData,
    SessionExecutionResult,
    SessionTransitionInfo,
)
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

if TYPE_CHECKING:
    from collections.abc import Sequence


def create_session_with_kernels(
    status: SessionStatus,
    scaling_group: str = "default",
    kernel_status: KernelStatus = KernelStatus.RUNNING,
    num_kernels: int = 1,
) -> SessionWithKernels:
    """Helper to create test SessionWithKernels."""
    session_id = SessionId(uuid4())
    creation_id = str(uuid4())
    access_key = "test-key"

    session_info = SessionInfo(
        identity=SessionIdentity(
            id=session_id,
            creation_id=creation_id,
            name="test-session",
            session_type=SessionTypes.INTERACTIVE,
            priority=0,
        ),
        metadata=SessionMetadata(
            name="test-session",
            domain_name="default",
            group_id=uuid4(),
            user_uuid=uuid4(),
            access_key=access_key,
            session_type=SessionTypes.INTERACTIVE,
            priority=0,
            created_at=None,
            tag=None,
        ),
        resource=ResourceSpec(
            cluster_mode="single-node",
            cluster_size=1,
            occupying_slots=ResourceSlot(),
            requested_slots=ResourceSlot(),
            scaling_group_name=scaling_group,
            target_sgroup_names=None,
            agent_ids=None,
        ),
        image=ImageSpec(images=None, tag=None),
        mounts=MountSpec(vfolder_mounts=None),
        execution=SessionExecution(
            environ=None,
            bootstrap_script=None,
            startup_command=None,
            use_host_network=False,
            callback_url=None,
        ),
        lifecycle=SessionLifecycle(
            status=status,
            result=SessionResult.UNDEFINED,
            created_at=None,
            terminated_at=None,
            starts_at=None,
            status_changed=None,
            batch_timeout=None,
            status_info=None,
            status_data=None,
            status_history=None,
        ),
        metrics=SessionMetrics(num_queries=0, last_stat=None),
        network=SessionNetwork(network_type=None, network_id=None),
    )

    kernel_infos = []
    for i in range(num_kernels):
        kernel_info = KernelInfo(
            id=KernelId(uuid4()),
            session=RelatedSessionInfo(
                session_id=str(session_id),
                creation_id=creation_id,
                name="test-session",
                session_type=SessionTypes.INTERACTIVE,
            ),
            user_permission=UserPermission(
                user_uuid=uuid4(),
                access_key=access_key,
                domain_name="default",
                group_id=uuid4(),
                uid=None,
                main_gid=None,
                gids=None,
            ),
            image=ImageInfo(identifier=None, registry=None, tag=None, architecture=None),
            network=NetworkConfig(
                kernel_host=None,
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                service_ports=None,
                preopen_ports=None,
                use_host_network=False,
            ),
            cluster=ClusterConfig(
                cluster_mode="single-node",
                cluster_size=1,
                cluster_role="main" if i == 0 else "sub",
                cluster_idx=i,
                local_rank=i,
                cluster_hostname="",
            ),
            resource=ResourceInfo(
                scaling_group=scaling_group,
                agent=None,
                agent_addr=None,
                container_id=None,
                occupied_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
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
                status=kernel_status,
                result=SessionResult.UNDEFINED,
                created_at=None,
                terminated_at=None,
                starts_at=None,
                status_changed=None,
                status_info=None,
                status_data=None,
                status_history=None,
                last_seen=None,
            ),
            metrics=Metrics(num_queries=0, last_stat=None, container_log=None),
            metadata=Metadata(callback_url=None, internal_data=None),
        )
        kernel_infos.append(kernel_info)

    return SessionWithKernels(session_info=session_info, kernel_infos=kernel_infos)


class TestCheckPullingProgressLifecycleHandler:
    """Tests for CheckPullingProgressLifecycleHandler."""

    @pytest.fixture
    def mock_event_producer(self) -> MagicMock:
        """Mock EventProducer."""
        mock = MagicMock()
        mock.broadcast_events_batch = AsyncMock()
        return mock

    @pytest.fixture
    def handler(self, mock_event_producer: MagicMock) -> CheckPullingProgressLifecycleHandler:
        """Create handler with mocked dependencies."""
        return CheckPullingProgressLifecycleHandler(mock_event_producer)

    def test_name(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test handler name."""
        assert handler.name() == "check-pulling-progress"

    def test_target_statuses(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test target statuses."""
        statuses = handler.target_statuses()
        assert SessionStatus.PREPARING in statuses
        assert SessionStatus.PULLING in statuses

    def test_target_kernel_statuses(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test target kernel statuses."""
        kernel_statuses = handler.target_kernel_statuses()
        assert kernel_statuses is not None
        assert KernelStatus.PREPARED in kernel_statuses
        assert KernelStatus.RUNNING in kernel_statuses

    def test_success_status(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test success status."""
        assert handler.success_status() == SessionStatus.PREPARED

    def test_failure_status(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test failure status (None for this handler)."""
        assert handler.failure_status() is None

    def test_stale_status(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test stale status (None for this handler)."""
        assert handler.stale_status() is None

    def test_lock_id(self, handler: CheckPullingProgressLifecycleHandler) -> None:
        """Test lock ID."""
        assert handler.lock_id == LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def test_execute_all_sessions_succeed(
        self, handler: CheckPullingProgressLifecycleHandler
    ) -> None:
        """Test execute marks all sessions as success."""
        sessions: Sequence[SessionWithKernels] = [
            create_session_with_kernels(
                SessionStatus.PREPARING,
                kernel_status=KernelStatus.PREPARED,
            ),
            create_session_with_kernels(
                SessionStatus.PULLING,
                kernel_status=KernelStatus.RUNNING,
            ),
        ]

        result = await handler.execute("default", sessions)

        assert len(result.successes) == 2
        assert len(result.failures) == 0
        assert len(result.stales) == 0
        assert len(result.scheduled_data) == 2

    async def test_execute_empty_sessions(
        self, handler: CheckPullingProgressLifecycleHandler
    ) -> None:
        """Test execute with empty sessions."""
        result = await handler.execute("default", [])

        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert len(result.stales) == 0

    async def test_execute_includes_correct_scheduled_data(
        self, handler: CheckPullingProgressLifecycleHandler
    ) -> None:
        """Test execute includes correct scheduled data for post-processing."""
        session = create_session_with_kernels(
            SessionStatus.PREPARING,
            kernel_status=KernelStatus.PREPARED,
        )
        sessions: Sequence[SessionWithKernels] = [session]

        result = await handler.execute("default", sessions)

        assert len(result.scheduled_data) == 1
        scheduled = result.scheduled_data[0]
        assert scheduled.session_id == session.session_info.identity.id
        assert scheduled.creation_id == session.session_info.identity.creation_id
        assert scheduled.access_key == session.session_info.metadata.access_key
        assert scheduled.reason == "triggered-by-scheduler"


class TestCheckCreatingProgressLifecycleHandler:
    """Tests for CheckCreatingProgressLifecycleHandler."""

    @pytest.fixture
    def mock_event_producer(self) -> MagicMock:
        """Mock EventProducer."""
        mock = MagicMock()
        mock.broadcast_events_batch = AsyncMock()
        return mock

    @pytest.fixture
    def mock_scheduling_controller(self) -> MagicMock:
        """Mock SchedulingController."""
        mock = MagicMock()
        mock.mark_scheduling_needed = AsyncMock()
        return mock

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Mock SchedulerRepository."""
        mock = MagicMock()
        mock.get_sessions_for_transition = AsyncMock(return_value=[])
        mock.update_sessions_to_running = AsyncMock()
        return mock

    @pytest.fixture
    def mock_hook_registry(self) -> MagicMock:
        """Mock HookRegistry."""
        mock = MagicMock()
        mock_hook = MagicMock()
        mock_hook.on_transition_to_running = AsyncMock(return_value=None)
        mock.get_hook = MagicMock(return_value=mock_hook)
        return mock

    @pytest.fixture
    def handler(
        self,
        mock_scheduling_controller: MagicMock,
        mock_event_producer: MagicMock,
        mock_repository: MagicMock,
        mock_hook_registry: MagicMock,
    ) -> CheckCreatingProgressLifecycleHandler:
        """Create handler with mocked dependencies."""
        return CheckCreatingProgressLifecycleHandler(
            mock_scheduling_controller,
            mock_event_producer,
            mock_repository,
            mock_hook_registry,
        )

    def test_name(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test handler name."""
        assert handler.name() == "check-creating-progress"

    def test_target_statuses(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test target statuses."""
        statuses = handler.target_statuses()
        assert statuses == [SessionStatus.CREATING]

    def test_target_kernel_statuses(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test target kernel statuses."""
        kernel_statuses = handler.target_kernel_statuses()
        assert kernel_statuses == [KernelStatus.RUNNING]

    def test_success_status(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test success status."""
        assert handler.success_status() == SessionStatus.RUNNING

    def test_failure_status(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test failure status (None - sessions stay in CREATING on failure)."""
        assert handler.failure_status() is None

    def test_lock_id(self, handler: CheckCreatingProgressLifecycleHandler) -> None:
        """Test lock ID."""
        assert handler.lock_id == LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def test_execute_empty_sessions(
        self, handler: CheckCreatingProgressLifecycleHandler
    ) -> None:
        """Test execute with empty sessions returns empty result."""
        result = await handler.execute("default", [])

        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert result.needs_post_processing() is False


class TestCheckTerminatingProgressLifecycleHandler:
    """Tests for CheckTerminatingProgressLifecycleHandler."""

    @pytest.fixture
    def mock_event_producer(self) -> MagicMock:
        """Mock EventProducer."""
        mock = MagicMock()
        mock.broadcast_events_batch = AsyncMock()
        return mock

    @pytest.fixture
    def mock_scheduling_controller(self) -> MagicMock:
        """Mock SchedulingController."""
        mock = MagicMock()
        mock.mark_scheduling_needed = AsyncMock()
        return mock

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Mock SchedulerRepository."""
        mock = MagicMock()
        mock.get_sessions_for_transition = AsyncMock(return_value=[])
        mock.update_sessions_to_terminated = AsyncMock()
        mock.invalidate_kernel_related_cache = AsyncMock()
        return mock

    @pytest.fixture
    def mock_hook_registry(self) -> MagicMock:
        """Mock HookRegistry."""
        mock = MagicMock()
        mock_hook = MagicMock()
        mock_hook.on_transition_to_terminated = AsyncMock(return_value=None)
        mock.get_hook = MagicMock(return_value=mock_hook)
        return mock

    @pytest.fixture
    def handler(
        self,
        mock_scheduling_controller: MagicMock,
        mock_event_producer: MagicMock,
        mock_repository: MagicMock,
        mock_hook_registry: MagicMock,
    ) -> CheckTerminatingProgressLifecycleHandler:
        """Create handler with mocked dependencies."""
        return CheckTerminatingProgressLifecycleHandler(
            mock_scheduling_controller,
            mock_event_producer,
            mock_repository,
            mock_hook_registry,
        )

    def test_name(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test handler name."""
        assert handler.name() == "check-terminating-progress"

    def test_target_statuses(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test target statuses."""
        statuses = handler.target_statuses()
        assert statuses == [SessionStatus.TERMINATING]

    def test_target_kernel_statuses(
        self, handler: CheckTerminatingProgressLifecycleHandler
    ) -> None:
        """Test target kernel statuses."""
        kernel_statuses = handler.target_kernel_statuses()
        assert kernel_statuses == [KernelStatus.TERMINATED]

    def test_success_status(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test success status."""
        assert handler.success_status() == SessionStatus.TERMINATED

    def test_failure_status(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test failure status (None - termination always proceeds)."""
        assert handler.failure_status() is None

    def test_lock_id(self, handler: CheckTerminatingProgressLifecycleHandler) -> None:
        """Test lock ID."""
        assert handler.lock_id == LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def test_execute_empty_sessions(
        self, handler: CheckTerminatingProgressLifecycleHandler
    ) -> None:
        """Test execute with empty sessions returns empty result."""
        result = await handler.execute("default", [])

        assert len(result.successes) == 0
        assert len(result.failures) == 0
        assert result.needs_post_processing() is False


class TestCheckRunningSessionTerminationLifecycleHandler:
    """Tests for CheckRunningSessionTerminationLifecycleHandler."""

    @pytest.fixture
    def mock_valkey_schedule(self) -> MagicMock:
        """Mock ValkeyScheduleClient."""
        mock = MagicMock()
        mock.mark_schedule_needed = AsyncMock()
        return mock

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Mock SchedulerRepository."""
        mock = MagicMock()
        mock.invalidate_kernel_related_cache = AsyncMock()
        return mock

    @pytest.fixture
    def handler(
        self,
        mock_valkey_schedule: MagicMock,
        mock_repository: MagicMock,
    ) -> CheckRunningSessionTerminationLifecycleHandler:
        """Create handler with mocked dependencies."""
        return CheckRunningSessionTerminationLifecycleHandler(
            mock_valkey_schedule,
            mock_repository,
        )

    def test_name(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test handler name."""
        assert handler.name() == "check-running-session-termination"

    def test_target_statuses(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test target statuses."""
        statuses = handler.target_statuses()
        assert statuses == [SessionStatus.RUNNING]

    def test_target_kernel_statuses(
        self, handler: CheckRunningSessionTerminationLifecycleHandler
    ) -> None:
        """Test target kernel statuses."""
        kernel_statuses = handler.target_kernel_statuses()
        assert kernel_statuses == [KernelStatus.TERMINATED]

    def test_success_status(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test success status."""
        assert handler.success_status() == SessionStatus.TERMINATING

    def test_failure_status(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test failure status (None for this handler)."""
        assert handler.failure_status() is None

    def test_stale_status(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test stale status (None for this handler)."""
        assert handler.stale_status() is None

    def test_lock_id(self, handler: CheckRunningSessionTerminationLifecycleHandler) -> None:
        """Test lock ID."""
        assert handler.lock_id == LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def test_execute_marks_sessions_for_termination(
        self, handler: CheckRunningSessionTerminationLifecycleHandler
    ) -> None:
        """Test execute marks RUNNING sessions with all kernels TERMINATED for termination."""
        sessions: Sequence[SessionWithKernels] = [
            create_session_with_kernels(
                SessionStatus.RUNNING,
                kernel_status=KernelStatus.TERMINATED,
            ),
            create_session_with_kernels(
                SessionStatus.RUNNING,
                kernel_status=KernelStatus.TERMINATED,
            ),
        ]

        result = await handler.execute("default", sessions)

        assert len(result.successes) == 2
        assert len(result.failures) == 0
        assert len(result.stales) == 0
        assert len(result.scheduled_data) == 2

    async def test_execute_empty_sessions(
        self, handler: CheckRunningSessionTerminationLifecycleHandler
    ) -> None:
        """Test execute with empty sessions."""
        result = await handler.execute("default", [])

        assert len(result.successes) == 0
        assert result.needs_post_processing() is False

    async def test_execute_scheduled_data_has_abnormal_reason(
        self, handler: CheckRunningSessionTerminationLifecycleHandler
    ) -> None:
        """Test execute sets ABNORMAL_TERMINATION as reason."""
        session = create_session_with_kernels(
            SessionStatus.RUNNING,
            kernel_status=KernelStatus.TERMINATED,
        )
        sessions: Sequence[SessionWithKernels] = [session]

        result = await handler.execute("default", sessions)

        assert len(result.scheduled_data) == 1
        assert result.scheduled_data[0].reason == "ABNORMAL_TERMINATION"


class TestSessionExecutionResult:
    """Tests for SessionExecutionResult dataclass."""

    def test_needs_post_processing_empty(self) -> None:
        """Test needs_post_processing returns False when empty."""
        result = SessionExecutionResult()
        assert result.needs_post_processing() is False

    def test_needs_post_processing_with_data(self) -> None:
        """Test needs_post_processing returns True with scheduled_data."""
        result = SessionExecutionResult()
        result.scheduled_data.append(
            ScheduledSessionData(
                session_id=SessionId(uuid4()),
                creation_id="test",
                access_key=AccessKey("test"),
                reason="test",
            )
        )
        assert result.needs_post_processing() is True

    def test_success_count(self) -> None:
        """Test success_count returns correct count."""
        result = SessionExecutionResult()
        result.successes.append(
            SessionTransitionInfo(
                session_id=SessionId(uuid4()), from_status=SessionStatus.PREPARING
            )
        )
        result.successes.append(
            SessionTransitionInfo(
                session_id=SessionId(uuid4()), from_status=SessionStatus.PREPARING
            )
        )
        assert result.success_count() == 2

    def test_merge(self) -> None:
        """Test merge combines two results."""
        result1 = SessionExecutionResult()
        result1.successes.append(
            SessionTransitionInfo(
                session_id=SessionId(uuid4()), from_status=SessionStatus.PREPARING
            )
        )

        result2 = SessionExecutionResult()
        result2.successes.append(
            SessionTransitionInfo(
                session_id=SessionId(uuid4()), from_status=SessionStatus.PREPARING
            )
        )
        result2.stales.append(
            SessionTransitionInfo(session_id=SessionId(uuid4()), from_status=SessionStatus.CREATING)
        )

        result1.merge(result2)

        assert len(result1.successes) == 2
        assert len(result1.stales) == 1
