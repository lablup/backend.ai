"""Shared fixtures for sokovan scheduler handler tests."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Optional
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    AgentId,
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
    KernelStatus,
    NetworkConfig,
    RelatedSessionInfo,
    ResourceInfo,
    RuntimeConfig,
    UserPermission,
)
from ai.backend.manager.data.kernel.types import (
    LifecycleStatus as KernelLifecycleStatus,
)
from ai.backend.manager.data.kernel.types import (
    Metadata as KernelMetadata,
)
from ai.backend.manager.data.kernel.types import (
    Metrics as KernelMetrics,
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
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.repositories.scheduler.types import ScheduledSessionData
from ai.backend.manager.repositories.scheduler.types.session import (
    TerminatingKernelData,
    TerminatingSessionData,
)
from ai.backend.manager.sokovan.data import (
    ImageConfigData,
    KernelBindingData,
    SessionDataForPull,
    SessionDataForStart,
    SessionsForPullWithImages,
    SessionsForStartWithImages,
    SessionWithKernels,
)
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult

# =============================================================================
# Internal Helper Functions (not fixtures)
# =============================================================================


def _create_session(
    session_id: Optional[SessionId] = None,
    status: SessionStatus = SessionStatus.PENDING,
    scaling_group: str = "default",
    access_key: str = "test-access-key",
    kernel_count: int = 1,
    kernel_status: KernelStatus = KernelStatus.PENDING,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
    phase_attempts: int = 0,
    phase_started_at: Optional[datetime] = None,
) -> SessionWithKernels:
    """Create SessionWithKernels with sensible defaults."""
    sid = session_id or SessionId(uuid4())
    creation_id = str(uuid4())
    user_uuid = uuid4()
    group_id = uuid4()
    now = datetime.now(tzutc())

    session_info = SessionInfo(
        identity=SessionIdentity(
            id=sid,
            creation_id=creation_id,
            name=f"session-{sid}",
            session_type=session_type,
            priority=0,
        ),
        metadata=SessionMetadata(
            name=f"session-{sid}",
            domain_name="default",
            group_id=group_id,
            user_uuid=user_uuid,
            access_key=access_key,
            session_type=session_type,
            priority=0,
            created_at=now,
            tag=None,
        ),
        resource=ResourceSpec(
            cluster_mode=cluster_mode.value,
            cluster_size=kernel_count,
            occupying_slots=ResourceSlot(),
            requested_slots=ResourceSlot(),
            scaling_group_name=scaling_group,
            target_sgroup_names=None,
            agent_ids=None,
        ),
        image=ImageSpec(images=["test-image:latest"], tag=None),
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
            created_at=now,
            terminated_at=None,
            starts_at=None,
            status_changed=now,
            batch_timeout=None,
            status_info=None,
            status_data=None,
            status_history=None,
        ),
        metrics=SessionMetrics(num_queries=0, last_stat=None),
        network=SessionNetwork(network_type=None, network_id=None),
    )

    kernel_infos = []
    for i in range(kernel_count):
        kernel_id = KernelId(uuid4())
        agent_id = AgentId(f"agent-{i}")
        kernel_info = KernelInfo(
            id=kernel_id,
            session=RelatedSessionInfo(
                session_id=str(sid),
                creation_id=creation_id,
                name=f"session-{sid}",
                session_type=session_type,
            ),
            user_permission=UserPermission(
                user_uuid=user_uuid,
                access_key=access_key,
                domain_name="default",
                group_id=group_id,
                uid=None,
                main_gid=None,
                gids=None,
            ),
            image=ImageInfo(
                identifier=None,
                registry="docker.io",
                tag="latest",
                architecture="x86_64",
            ),
            network=NetworkConfig(
                kernel_host=None,
                repl_in_port=2000,
                repl_out_port=2001,
                stdin_port=2002,
                stdout_port=2003,
                service_ports=None,
                preopen_ports=None,
                use_host_network=False,
            ),
            cluster=ClusterConfig(
                cluster_mode=cluster_mode.value,
                cluster_size=kernel_count,
                cluster_role=DEFAULT_ROLE if i == 0 else f"sub{i}",
                cluster_idx=i,
                local_rank=0,
                cluster_hostname=f"kernel-{i}",
            ),
            resource=ResourceInfo(
                scaling_group=scaling_group,
                agent=agent_id,
                agent_addr=f"tcp://agent-{i}:5001",
                container_id=f"container-{kernel_id}",
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
            lifecycle=KernelLifecycleStatus(
                status=kernel_status,
                result=SessionResult.UNDEFINED,
                created_at=now,
                terminated_at=None,
                starts_at=None,
                status_changed=now,
                status_info=None,
                status_data=None,
                status_history=None,
                last_seen=None,
                last_observed_at=None,
            ),
            metrics=KernelMetrics(num_queries=0, last_stat=None, container_log=None),
            metadata=KernelMetadata(callback_url=None, internal_data=None),
        )
        kernel_infos.append(kernel_info)

    return SessionWithKernels(
        session_info=session_info,
        kernel_infos=kernel_infos,
        phase_attempts=phase_attempts,
        phase_started_at=phase_started_at,
    )


def _create_kernel(
    kernel_id: Optional[KernelId] = None,
    status: KernelStatus = KernelStatus.RUNNING,
    agent_id: Optional[AgentId] = None,
    agent_addr: Optional[str] = None,
    scaling_group: str = "default",
) -> KernelInfo:
    """Create KernelInfo with sensible defaults."""
    kid = kernel_id or KernelId(uuid4())
    aid = agent_id or AgentId(f"agent-{uuid4().hex[:8]}")
    now = datetime.now(tzutc())
    user_uuid = uuid4()
    group_id = uuid4()
    session_id = SessionId(uuid4())

    return KernelInfo(
        id=kid,
        session=RelatedSessionInfo(
            session_id=str(session_id),
            creation_id=str(uuid4()),
            name=f"session-{session_id}",
            session_type=SessionTypes.INTERACTIVE,
        ),
        user_permission=UserPermission(
            user_uuid=user_uuid,
            access_key="test-access-key",
            domain_name="default",
            group_id=group_id,
            uid=None,
            main_gid=None,
            gids=None,
        ),
        image=ImageInfo(
            identifier=None,
            registry="docker.io",
            tag="latest",
            architecture="x86_64",
        ),
        network=NetworkConfig(
            kernel_host=None,
            repl_in_port=2000,
            repl_out_port=2001,
            stdin_port=2002,
            stdout_port=2003,
            service_ports=None,
            preopen_ports=None,
            use_host_network=False,
        ),
        cluster=ClusterConfig(
            cluster_mode=ClusterMode.SINGLE_NODE.value,
            cluster_size=1,
            cluster_role=DEFAULT_ROLE,
            cluster_idx=0,
            local_rank=0,
            cluster_hostname="kernel-0",
        ),
        resource=ResourceInfo(
            scaling_group=scaling_group,
            agent=aid,
            agent_addr=agent_addr or f"tcp://{aid}:5001",
            container_id=f"container-{kid}",
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
        lifecycle=KernelLifecycleStatus(
            status=status,
            result=SessionResult.UNDEFINED,
            created_at=now,
            terminated_at=None,
            starts_at=None,
            status_changed=now,
            status_info=None,
            status_data=None,
            status_history=None,
            last_seen=None,
            last_observed_at=None,
        ),
        metrics=KernelMetrics(num_queries=0, last_stat=None, container_log=None),
        metadata=KernelMetadata(callback_url=None, internal_data=None),
    )


# =============================================================================
# Mock Dependency Fixtures
# =============================================================================


@pytest.fixture
def mock_provisioner() -> AsyncMock:
    """Mock SessionProvisioner for ScheduleSessionsLifecycleHandler tests."""
    provisioner = AsyncMock()
    provisioner.schedule_scaling_group = AsyncMock(
        return_value=ScheduleResult(scheduled_sessions=[])
    )
    return provisioner


@pytest.fixture
def mock_launcher() -> AsyncMock:
    """Mock SessionLauncher for CheckPrecondition and StartSessions handlers."""
    launcher = AsyncMock()
    launcher.trigger_image_pulling = AsyncMock(return_value=None)
    launcher.start_sessions_for_handler = AsyncMock(return_value=None)
    return launcher


@pytest.fixture
def mock_terminator() -> AsyncMock:
    """Mock SessionTerminator for TerminateSessions and SweepStaleKernels handlers."""
    terminator = AsyncMock()
    terminator.terminate_sessions_for_handler = AsyncMock(return_value=None)
    terminator.check_stale_kernels = AsyncMock(return_value=[])
    return terminator


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock SchedulerRepository for handler tests."""
    repository = AsyncMock()
    repository.get_scheduling_data = AsyncMock(return_value=None)
    repository.get_sessions_for_pull_by_ids = AsyncMock(
        return_value=SessionsForPullWithImages(sessions=[], image_configs={})
    )
    repository.search_sessions_with_kernels_and_user = AsyncMock(
        return_value=SessionsForStartWithImages(sessions=[], image_configs={})
    )
    repository.get_terminating_sessions_by_ids = AsyncMock(return_value=[])
    return repository


# =============================================================================
# Pre-created Session Fixtures for ScheduleSessionsLifecycleHandler
# =============================================================================


@pytest.fixture
def pending_session() -> SessionWithKernels:
    """Single PENDING session for basic scheduling tests."""
    return _create_session(status=SessionStatus.PENDING)


@pytest.fixture
def pending_sessions_multiple() -> list[SessionWithKernels]:
    """Multiple PENDING sessions for batch scheduling tests."""
    return [
        _create_session(status=SessionStatus.PENDING),
        _create_session(status=SessionStatus.PENDING),
        _create_session(status=SessionStatus.PENDING),
    ]


# =============================================================================
# Pre-created Session Fixtures for CheckPreconditionLifecycleHandler
# =============================================================================


@pytest.fixture
def scheduled_session() -> SessionWithKernels:
    """Single SCHEDULED session for precondition check tests."""
    return _create_session(
        status=SessionStatus.SCHEDULED,
        kernel_status=KernelStatus.SCHEDULED,
    )


@pytest.fixture
def scheduled_sessions_multiple() -> list[SessionWithKernels]:
    """Multiple SCHEDULED sessions for batch precondition tests."""
    return [
        _create_session(status=SessionStatus.SCHEDULED, kernel_status=KernelStatus.SCHEDULED),
        _create_session(status=SessionStatus.SCHEDULED, kernel_status=KernelStatus.SCHEDULED),
    ]


# =============================================================================
# Pre-created Session Fixtures for StartSessionsLifecycleHandler
# =============================================================================


@pytest.fixture
def prepared_session() -> SessionWithKernels:
    """Single PREPARED session for start tests."""
    return _create_session(
        status=SessionStatus.PREPARED,
        kernel_status=KernelStatus.PREPARED,
    )


@pytest.fixture
def prepared_sessions_multiple() -> list[SessionWithKernels]:
    """Multiple PREPARED sessions for batch start tests."""
    return [
        _create_session(status=SessionStatus.PREPARED, kernel_status=KernelStatus.PREPARED),
        _create_session(status=SessionStatus.PREPARED, kernel_status=KernelStatus.PREPARED),
    ]


# =============================================================================
# Pre-created Session Fixtures for TerminateSessionsLifecycleHandler
# =============================================================================


@pytest.fixture
def terminating_session() -> SessionWithKernels:
    """Single TERMINATING session for termination tests."""
    return _create_session(
        status=SessionStatus.TERMINATING,
        kernel_status=KernelStatus.RUNNING,
    )


@pytest.fixture
def terminating_sessions_multiple() -> list[SessionWithKernels]:
    """Multiple TERMINATING sessions for batch termination tests."""
    return [
        _create_session(status=SessionStatus.TERMINATING, kernel_status=KernelStatus.RUNNING),
        _create_session(status=SessionStatus.TERMINATING, kernel_status=KernelStatus.RUNNING),
    ]


# =============================================================================
# Pre-created Kernel Fixtures for SweepStaleKernelsKernelHandler
# =============================================================================


@pytest.fixture
def running_kernel() -> KernelInfo:
    """Single RUNNING kernel for stale kernel tests."""
    return _create_kernel(status=KernelStatus.RUNNING)


@pytest.fixture
def running_kernels_multiple() -> list[KernelInfo]:
    """Multiple RUNNING kernels for batch stale kernel tests."""
    return [
        _create_kernel(status=KernelStatus.RUNNING),
        _create_kernel(status=KernelStatus.RUNNING),
        _create_kernel(status=KernelStatus.RUNNING),
    ]


@pytest.fixture
def running_kernels_five() -> list[KernelInfo]:
    """Five RUNNING kernels for mixed results tests."""
    return [
        _create_kernel(status=KernelStatus.RUNNING),
        _create_kernel(status=KernelStatus.RUNNING),
        _create_kernel(status=KernelStatus.RUNNING),
        _create_kernel(status=KernelStatus.RUNNING),
        _create_kernel(status=KernelStatus.RUNNING),
    ]


@pytest.fixture
def kernel_without_agent() -> KernelInfo:
    """Kernel without agent for edge case tests."""
    kernel = _create_kernel(status=KernelStatus.RUNNING)
    # Override resource to remove agent
    return KernelInfo(
        id=kernel.id,
        session=kernel.session,
        user_permission=kernel.user_permission,
        image=kernel.image,
        network=kernel.network,
        cluster=kernel.cluster,
        resource=ResourceInfo(
            scaling_group=kernel.resource.scaling_group,
            agent=None,  # No agent assigned
            agent_addr=None,
            container_id=None,
            occupied_slots=ResourceSlot(),
            requested_slots=ResourceSlot(),
            occupied_shares={},
            attached_devices={},
            resource_opts={},
        ),
        runtime=kernel.runtime,
        lifecycle=kernel.lifecycle,
        metrics=kernel.metrics,
        metadata=kernel.metadata,
    )


# =============================================================================
# Mock Response Fixtures (factories for creating mock responses from sessions)
# =============================================================================


@pytest.fixture
def schedule_result_success_factory() -> Callable[..., ScheduleResult]:
    """Factory for creating successful ScheduleResult from sessions."""

    def _create(sessions: list[SessionWithKernels]) -> ScheduleResult:
        scheduled_sessions = [
            ScheduledSessionData(
                session_id=s.session_info.identity.id,
                creation_id=s.session_info.identity.creation_id,
                access_key=AccessKey(s.session_info.metadata.access_key),
                reason="scheduled-successfully",
            )
            for s in sessions
        ]
        return ScheduleResult(scheduled_sessions=scheduled_sessions)

    return _create


@pytest.fixture
def sessions_for_pull_factory() -> Callable[..., SessionsForPullWithImages]:
    """Factory for creating SessionsForPullWithImages from sessions."""

    def _create(sessions: list[SessionWithKernels]) -> SessionsForPullWithImages:
        sessions_for_pull = [
            SessionDataForPull(
                session_id=s.session_info.identity.id,
                creation_id=s.session_info.identity.creation_id,
                access_key=AccessKey(s.session_info.metadata.access_key),
                kernels=[
                    KernelBindingData(
                        kernel_id=KernelId(k.id),
                        agent_id=AgentId(k.resource.agent) if k.resource.agent else None,
                        agent_addr=k.resource.agent_addr,
                        scaling_group=s.session_info.resource.scaling_group_name or "default",
                        image="test-image:latest",
                        architecture=k.image.architecture or "x86_64",
                    )
                    for k in s.kernel_infos
                ],
            )
            for s in sessions
        ]
        return SessionsForPullWithImages(
            sessions=sessions_for_pull,
            image_configs={
                "test-image:latest": ImageConfigData(
                    canonical="test-image:latest",
                    architecture="x86_64",
                    project=None,
                    is_local=False,
                    digest="sha256:abc123",
                    labels={},
                    registry_name="docker.io",
                    registry_url="https://registry-1.docker.io",
                    registry_username=None,
                    registry_password=None,
                )
            },
        )

    return _create


@pytest.fixture
def sessions_for_start_factory() -> Callable[..., SessionsForStartWithImages]:
    """Factory for creating SessionsForStartWithImages from sessions."""

    def _create(sessions: list[SessionWithKernels]) -> SessionsForStartWithImages:
        sessions_for_start = [
            SessionDataForStart(
                session_id=s.session_info.identity.id,
                creation_id=s.session_info.identity.creation_id,
                access_key=AccessKey(s.session_info.metadata.access_key),
                session_type=s.session_info.identity.session_type,
                name=s.session_info.identity.name,
                cluster_mode=ClusterMode(s.session_info.resource.cluster_mode),
                kernels=[
                    KernelBindingData(
                        kernel_id=KernelId(k.id),
                        agent_id=AgentId(k.resource.agent) if k.resource.agent else None,
                        agent_addr=k.resource.agent_addr,
                        scaling_group=s.session_info.resource.scaling_group_name or "default",
                        image="test-image:latest",
                        architecture=k.image.architecture or "x86_64",
                    )
                    for k in s.kernel_infos
                ],
                user_uuid=s.session_info.metadata.user_uuid,
                user_email="test@example.com",
                user_name="test-user",
                environ={},
            )
            for s in sessions
        ]
        return SessionsForStartWithImages(
            sessions=sessions_for_start,
            image_configs={
                "test-image:latest": ImageConfigData(
                    canonical="test-image:latest",
                    architecture="x86_64",
                    project=None,
                    is_local=False,
                    digest="sha256:abc123",
                    labels={},
                    registry_name="docker.io",
                    registry_url="https://registry-1.docker.io",
                    registry_username=None,
                    registry_password=None,
                )
            },
        )

    return _create


@pytest.fixture
def terminating_session_data_factory() -> Callable[..., list[TerminatingSessionData]]:
    """Factory for creating TerminatingSessionData list from sessions."""

    def _create(sessions: list[SessionWithKernels]) -> list[TerminatingSessionData]:
        return [
            TerminatingSessionData(
                session_id=s.session_info.identity.id,
                access_key=AccessKey(s.session_info.metadata.access_key),
                creation_id=s.session_info.identity.creation_id,
                status=s.session_info.lifecycle.status,
                status_info="user-requested",
                session_type=s.session_info.identity.session_type,
                kernels=[
                    TerminatingKernelData(
                        kernel_id=KernelId(k.id),
                        status=k.lifecycle.status,
                        container_id=k.resource.container_id,
                        agent_id=AgentId(k.resource.agent) if k.resource.agent else None,
                        agent_addr=k.resource.agent_addr,
                        occupied_slots=k.resource.occupied_slots or ResourceSlot(),
                    )
                    for k in s.kernel_infos
                ],
            )
            for s in sessions
        ]

    return _create
