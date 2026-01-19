"""Fixtures for launcher tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AutoPullBehavior,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.sokovan.scheduler.launcher.launcher import (
    SessionLauncher,
    SessionLauncherArgs,
)
from ai.backend.manager.sokovan.scheduler.types import (
    ImageConfigData,
    KernelBindingData,
    SessionDataForPull,
    SessionDataForStart,
)

# =============================================================================
# Mock Dependencies
# =============================================================================


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock SchedulerRepository for launcher tests."""
    repository = AsyncMock()
    repository.update_session_error_info = AsyncMock(return_value=None)
    repository.update_session_network_id = AsyncMock(return_value=None)
    return repository


@pytest.fixture
def mock_agent_client_pool() -> MagicMock:
    """Mock AgentClientPool with async context manager support."""
    pool = MagicMock()

    mock_client = AsyncMock()
    mock_client.check_and_pull = AsyncMock(return_value={})
    mock_client.create_kernels = AsyncMock(return_value=None)
    mock_client.create_local_network = AsyncMock(return_value=None)
    mock_client.assign_port = AsyncMock(return_value=22000)

    @asynccontextmanager
    async def acquire(agent_id: AgentId) -> AsyncGenerator[AsyncMock, None]:
        yield mock_client

    pool.acquire = MagicMock(side_effect=acquire)
    pool._mock_client = mock_client  # For assertion access
    return pool


@pytest.fixture
def mock_network_plugin_ctx() -> MagicMock:
    """Mock NetworkPluginContext."""
    ctx = MagicMock()
    mock_plugin = MagicMock()
    mock_network_info = MagicMock()
    mock_network_info.network_id = "test-network-id"
    mock_network_info.options = {}
    mock_plugin.create_network = AsyncMock(return_value=mock_network_info)
    ctx.plugins = {"overlay": mock_plugin}
    return ctx


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Mock ManagerConfigProvider."""
    provider = MagicMock()
    provider.config.docker.image.auto_pull.value = AutoPullBehavior.DIGEST.value
    provider.config.network.inter_container.default_driver = "overlay"
    provider.config.debug.enabled = False
    return provider


@pytest.fixture
def mock_valkey_schedule() -> AsyncMock:
    """Mock ValkeyScheduleClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def launcher(
    mock_repository: AsyncMock,
    mock_agent_client_pool: MagicMock,
    mock_network_plugin_ctx: MagicMock,
    mock_config_provider: MagicMock,
    mock_valkey_schedule: AsyncMock,
) -> SessionLauncher:
    """Create SessionLauncher with mocked dependencies."""
    return SessionLauncher(
        SessionLauncherArgs(
            repository=mock_repository,
            agent_client_pool=mock_agent_client_pool,
            network_plugin_ctx=mock_network_plugin_ctx,
            config_provider=mock_config_provider,
            valkey_schedule=mock_valkey_schedule,
        )
    )


# =============================================================================
# Session Data Fixtures - Image Pulling
# =============================================================================


def _create_kernel_binding_data(
    kernel_id: KernelId | None = None,
    agent_id: AgentId | None = None,
    image: str = "cr.backend.ai/stable/python:3.9-ubuntu20.04",
    cluster_role: str = "main",
    cluster_idx: int = 0,
) -> KernelBindingData:
    """Create KernelBindingData for tests."""
    return KernelBindingData(
        kernel_id=kernel_id or KernelId(uuid4()),
        agent_id=agent_id or AgentId("agent-1"),
        agent_addr="tcp://agent-1:6001",
        image=image,
        architecture="x86_64",
        cluster_role=cluster_role,
        cluster_idx=cluster_idx,
        local_rank=0,
        cluster_hostname=f"{cluster_role}{cluster_idx}",
        requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
        uid=1000,
        main_gid=1000,
        gids=[1000],
        resource_opts={},
        vfolder_mounts=[],
        bootstrap_script=None,
        startup_command=None,
        internal_data={},
        preopen_ports=[],
        scaling_group="default",
    )


def _create_session_for_pull(
    session_id: SessionId | None = None,
    kernels: list[KernelBindingData] | None = None,
) -> SessionDataForPull:
    """Create SessionDataForPull for image pulling tests."""
    if kernels is None:
        kernels = [_create_kernel_binding_data()]

    return SessionDataForPull(
        session_id=session_id or SessionId(uuid4()),
        creation_id=str(uuid4()),
        access_key=AccessKey("test-key"),
        kernels=kernels,
    )


@pytest.fixture
def session_for_pull_single_kernel() -> SessionDataForPull:
    """Single session with one kernel for image pulling."""
    return _create_session_for_pull()


@pytest.fixture
def sessions_for_pull_multiple() -> list[SessionDataForPull]:
    """Multiple sessions with kernels on different agents."""
    return [
        _create_session_for_pull(
            kernels=[
                _create_kernel_binding_data(agent_id=AgentId("agent-1")),
            ]
        ),
        _create_session_for_pull(
            kernels=[
                _create_kernel_binding_data(agent_id=AgentId("agent-2")),
            ]
        ),
    ]


@pytest.fixture
def session_for_pull_multiple_kernels_same_agent() -> SessionDataForPull:
    """Session with multiple kernels on the same agent."""
    agent_id = AgentId("agent-1")
    return _create_session_for_pull(
        kernels=[
            _create_kernel_binding_data(agent_id=agent_id, image="image-1"),
            _create_kernel_binding_data(agent_id=agent_id, image="image-2"),
        ]
    )


@pytest.fixture
def session_for_pull_duplicate_images() -> SessionDataForPull:
    """Session with duplicate images (should be deduplicated)."""
    agent_id = AgentId("agent-1")
    image = "cr.backend.ai/stable/python:3.9-ubuntu20.04"
    return _create_session_for_pull(
        kernels=[
            _create_kernel_binding_data(agent_id=agent_id, image=image),
            _create_kernel_binding_data(agent_id=agent_id, image=image),
        ]
    )


# =============================================================================
# Session Data Fixtures - Session Starting
# =============================================================================


def _create_session_for_start(
    session_id: SessionId | None = None,
    kernels: list[KernelBindingData] | None = None,
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
    network_type: NetworkType | None = None,
) -> SessionDataForStart:
    """Create SessionDataForStart for session start tests."""
    if kernels is None:
        kernels = [_create_kernel_binding_data()]

    return SessionDataForStart(
        session_id=session_id or SessionId(uuid4()),
        creation_id=str(uuid4()),
        access_key=AccessKey("test-key"),
        session_type=SessionTypes.INTERACTIVE,
        name="test-session",
        user_uuid=uuid4(),
        user_email="test@example.com",
        user_name="testuser",
        cluster_mode=cluster_mode,
        network_type=network_type or NetworkType.VOLATILE,
        network_id=None,
        kernels=kernels,
        environ={},
    )


@pytest.fixture
def session_for_start_single_kernel() -> SessionDataForStart:
    """Single session with one kernel for starting."""
    return _create_session_for_start()


@pytest.fixture
def session_for_start_multi_kernel() -> SessionDataForStart:
    """Session with multiple kernels (cluster session)."""
    return _create_session_for_start(
        kernels=[
            _create_kernel_binding_data(cluster_role="main", cluster_idx=0),
            _create_kernel_binding_data(cluster_role="sub", cluster_idx=1),
        ]
    )


@pytest.fixture
def session_for_start_multi_node() -> SessionDataForStart:
    """Multi-node cluster session."""
    return _create_session_for_start(
        kernels=[
            _create_kernel_binding_data(agent_id=AgentId("agent-1"), cluster_idx=0),
            _create_kernel_binding_data(agent_id=AgentId("agent-2"), cluster_idx=1),
        ],
        cluster_mode=ClusterMode.MULTI_NODE,
    )


@pytest.fixture
def session_for_start_no_kernels() -> SessionDataForStart:
    """Session with no kernels (error case)."""
    return _create_session_for_start(kernels=[])


@pytest.fixture
def session_for_start_host_network() -> SessionDataForStart:
    """Session with host network type."""
    return _create_session_for_start(
        kernels=[
            _create_kernel_binding_data(cluster_idx=0),
            _create_kernel_binding_data(cluster_idx=1),
        ],
        network_type=NetworkType.HOST,
    )


@pytest.fixture
def session_for_start_kernel_no_agent() -> SessionDataForStart:
    """Session with kernel that has no agent assigned."""
    kernel = _create_kernel_binding_data()
    kernel.agent_id = None  # type: ignore[assignment]
    return _create_session_for_start(kernels=[kernel])


# =============================================================================
# Image Config Fixtures
# =============================================================================


def _create_image_config_data(
    canonical: str = "cr.backend.ai/stable/python:3.9-ubuntu20.04",
) -> ImageConfigData:
    """Create ImageConfigData for tests."""
    return ImageConfigData(
        canonical=canonical,
        architecture="x86_64",
        project="stable",
        is_local=False,
        digest="sha256:abc123",
        labels={},
        registry_name="cr.backend.ai",
        registry_url="https://cr.backend.ai",
        registry_username=None,
        registry_password=None,
    )


@pytest.fixture
def image_config_default() -> dict[str, ImageConfigData]:
    """Default image configuration."""
    return {
        "cr.backend.ai/stable/python:3.9-ubuntu20.04": _create_image_config_data(),
    }


@pytest.fixture
def image_configs_multiple() -> dict[str, ImageConfigData]:
    """Multiple image configurations."""
    return {
        "image-1": _create_image_config_data(canonical="image-1"),
        "image-2": _create_image_config_data(canonical="image-2"),
    }
