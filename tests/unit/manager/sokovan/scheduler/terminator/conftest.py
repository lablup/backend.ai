"""Fixtures for terminator tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule import HealthCheckStatus
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
from ai.backend.manager.models.session import SessionStatus
from ai.backend.manager.repositories.scheduler import (
    TerminatingKernelData,
    TerminatingSessionData,
)
from ai.backend.manager.sokovan.scheduler.terminator.terminator import (
    SessionTerminator,
    SessionTerminatorArgs,
)

# =============================================================================
# Mock Dependencies
# =============================================================================


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock SchedulerRepository for terminator tests."""
    return AsyncMock()


@pytest.fixture
def mock_agent_client_pool() -> MagicMock:
    """Mock AgentClientPool with async context manager support."""
    pool = MagicMock()

    mock_client = AsyncMock()
    mock_client.destroy_kernel = AsyncMock(return_value=None)
    mock_client.check_running = AsyncMock(return_value=False)

    @asynccontextmanager
    async def acquire(agent_id: AgentId) -> AsyncGenerator[AsyncMock, None]:
        yield mock_client

    pool.acquire = MagicMock(side_effect=acquire)
    pool._mock_client = mock_client  # For assertion access
    return pool


@pytest.fixture
def mock_valkey_schedule() -> AsyncMock:
    """Mock ValkeyScheduleClient."""
    client = AsyncMock()
    client.check_kernel_presence_status_batch = AsyncMock(return_value={})
    return client


@pytest.fixture
def terminator(
    mock_repository: AsyncMock,
    mock_agent_client_pool: MagicMock,
    mock_valkey_schedule: AsyncMock,
) -> SessionTerminator:
    """Create SessionTerminator with mocked dependencies."""
    return SessionTerminator(
        SessionTerminatorArgs(
            repository=mock_repository,
            agent_client_pool=mock_agent_client_pool,
            valkey_schedule=mock_valkey_schedule,
        )
    )


# =============================================================================
# Session Data Fixtures - Termination
# =============================================================================


def _create_terminating_kernel_data(
    kernel_id: KernelId | None = None,
    agent_id: AgentId | None = None,
) -> TerminatingKernelData:
    """Create TerminatingKernelData for termination tests."""
    return TerminatingKernelData(
        kernel_id=kernel_id or KernelId(uuid4()),
        status=KernelStatus.RUNNING,
        container_id=str(uuid4()),
        agent_id=agent_id or AgentId("agent-1"),
        agent_addr="tcp://agent-1:6001",
        occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
    )


def _create_terminating_session_data(
    session_id: SessionId | None = None,
    kernels: list[TerminatingKernelData] | None = None,
    status_info: str = "user-requested",
) -> TerminatingSessionData:
    """Create TerminatingSessionData for termination tests."""
    if kernels is None:
        kernels = [_create_terminating_kernel_data()]

    return TerminatingSessionData(
        session_id=session_id or SessionId(uuid4()),
        access_key=AccessKey("test-key"),
        creation_id=str(uuid4()),
        status=SessionStatus.TERMINATING,
        status_info=status_info,
        session_type=SessionTypes.INTERACTIVE,
        kernels=kernels,
    )


@pytest.fixture
def terminating_session_single_kernel() -> TerminatingSessionData:
    """Single session with one kernel for termination."""
    return _create_terminating_session_data()


@pytest.fixture
def terminating_session_multi_kernel() -> TerminatingSessionData:
    """Session with multiple kernels for termination."""
    return _create_terminating_session_data(
        kernels=[
            _create_terminating_kernel_data(agent_id=AgentId("agent-1")),
            _create_terminating_kernel_data(agent_id=AgentId("agent-2")),
        ]
    )


@pytest.fixture
def terminating_sessions_multiple() -> list[TerminatingSessionData]:
    """Multiple sessions for termination."""
    return [
        _create_terminating_session_data(),
        _create_terminating_session_data(),
    ]


@pytest.fixture
def terminating_session_kernel_no_agent() -> TerminatingSessionData:
    """Session with kernel that has no agent assigned."""
    kernel = _create_terminating_kernel_data()
    kernel.agent_id = None  # type: ignore[assignment]
    return _create_terminating_session_data(kernels=[kernel])


@pytest.fixture
def terminating_session_mixed_agents() -> TerminatingSessionData:
    """Session with kernels, some with agents, some without."""
    kernel_with_agent = _create_terminating_kernel_data()
    kernel_without_agent = _create_terminating_kernel_data()
    kernel_without_agent.agent_id = None  # type: ignore[assignment]
    return _create_terminating_session_data(kernels=[kernel_with_agent, kernel_without_agent])


# =============================================================================
# Kernel Data Fixtures - Stale Detection
# =============================================================================


def _create_kernel_info(
    kernel_id: UUID | None = None,
    agent_id: str | None = "agent-1",
    status: KernelStatus = KernelStatus.RUNNING,
) -> KernelInfo:
    """Create KernelInfo for stale detection tests."""
    kid = KernelId(kernel_id or uuid4())
    aid = agent_id  # Use as-is to allow explicit None
    now = datetime.now(tzutc())

    return KernelInfo(
        id=kid,
        session=RelatedSessionInfo(
            session_id=str(uuid4()),
            creation_id=str(uuid4()),
            name="test-session",
            session_type=SessionTypes.INTERACTIVE,
        ),
        user_permission=UserPermission(
            user_uuid=uuid4(),
            access_key="test-access-key",
            domain_name="default",
            group_id=uuid4(),
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
            cluster_role="main",
            cluster_idx=0,
            local_rank=0,
            cluster_hostname="kernel-0",
        ),
        resource=ResourceInfo(
            scaling_group="default",
            agent=aid,
            agent_addr=f"tcp://{aid}:5001" if aid else None,
            container_id=f"container-{kid}",
            occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
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
        ),
        metrics=KernelMetrics(num_queries=0, last_stat=None, container_log=None),
        metadata=KernelMetadata(callback_url=None, internal_data=None),
    )


@pytest.fixture
def running_kernel() -> KernelInfo:
    """Single RUNNING kernel."""
    return _create_kernel_info()


@pytest.fixture
def running_kernels_multiple() -> list[KernelInfo]:
    """Multiple RUNNING kernels on different agents."""
    return [
        _create_kernel_info(agent_id="agent-1"),
        _create_kernel_info(agent_id="agent-2"),
    ]


@pytest.fixture
def running_kernel_no_agent() -> KernelInfo:
    """RUNNING kernel with no agent assigned."""
    return _create_kernel_info(agent_id=None)


# =============================================================================
# Valkey Response Fixtures
# =============================================================================


@pytest.fixture
def valkey_all_alive_response(
    running_kernels_multiple: list[KernelInfo],
) -> dict[KernelId, MagicMock]:
    """Valkey response showing all kernels alive."""
    response = {}
    for kernel in running_kernels_multiple:
        mock_status = MagicMock()
        mock_status.presence = HealthCheckStatus.HEALTHY
        response[KernelId(kernel.id)] = mock_status
    return response


@pytest.fixture
def valkey_one_stale_response(
    running_kernels_multiple: list[KernelInfo],
) -> dict[KernelId, MagicMock]:
    """Valkey response showing first kernel as stale."""
    response = {}
    for i, kernel in enumerate(running_kernels_multiple):
        mock_status = MagicMock()
        if i == 0:
            mock_status.presence = HealthCheckStatus.STALE
        else:
            mock_status.presence = HealthCheckStatus.HEALTHY
        response[KernelId(kernel.id)] = mock_status
    return response


@pytest.fixture
def valkey_all_stale_response(
    running_kernels_multiple: list[KernelInfo],
) -> dict[KernelId, MagicMock]:
    """Valkey response showing all kernels as stale."""
    response = {}
    for kernel in running_kernels_multiple:
        mock_status = MagicMock()
        mock_status.presence = HealthCheckStatus.STALE
        response[KernelId(kernel.id)] = mock_status
    return response
