"""Fixtures for launcher tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.network import NetworkID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ArchName,
    AutoPullBehavior,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.network.types import NetworkData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.sokovan.scheduler.launcher.launcher import (
    SessionLauncher,
    SessionLauncherArgs,
)
from ai.backend.manager.views.sokovan.image import ImageConfigData
from ai.backend.manager.views.sokovan.lifecycle import (
    KernelBindingData,
    SessionDataForPull,
    SessionDataForStart,
)

# Shared image IDs for linking kernel <-> image config in tests
_DEFAULT_IMAGE_ID = UUID("00000000-0000-0000-0000-000000000001")
_IMAGE_ID_1 = UUID("00000000-0000-0000-0000-000000000002")
_IMAGE_ID_2 = UUID("00000000-0000-0000-0000-000000000003")

# A persistent network row: the id stored on the session and the plugin-generated
# container network name are unrelated values.
_PERSISTENT_NETWORK_ID = NetworkID(UUID("00000000-0000-0000-0000-0000000000a1"))
_PERSISTENT_NETWORK_REF_NAME = "bai-multinode-00000000-0000-0000-0000-0000000000b2-nw"

# =============================================================================
# Mock Dependencies
# =============================================================================


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock SchedulerRepository for launcher tests."""
    repository = AsyncMock()
    repository.update_session_error_info = AsyncMock(return_value=None)
    repository.update_session_network_id = AsyncMock(return_value=None)

    persistent_network = NetworkData(
        id=_PERSISTENT_NETWORK_ID,
        name="testnet",
        ref_name=_PERSISTENT_NETWORK_REF_NAME,
        driver="overlay",
        project_id=ProjectID(uuid4()),
        domain_name="default",
        options={"mode": "overlay", "network_name": _PERSISTENT_NETWORK_REF_NAME},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=None,
    )

    async def get_attached_network(network_id: str) -> NetworkData:
        if network_id != str(_PERSISTENT_NETWORK_ID):
            raise ObjectNotFound(object_name="network")
        return persistent_network

    repository.get_attached_network = AsyncMock(side_effect=get_attached_network)
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
    return AsyncMock()


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
    image_id: UUID | None = _DEFAULT_IMAGE_ID,
    cluster_role: str = "main",
    cluster_idx: int = 0,
) -> KernelBindingData:
    """Create KernelBindingData for tests."""
    return KernelBindingData(
        kernel_id=kernel_id or KernelId(uuid4()),
        agent_id=agent_id or AgentId("agent-1"),
        agent_addr="tcp://agent-1:6001",
        image=image,
        image_id=image_id,
        architecture=ArchName("x86_64"),
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
        resource_group="default",
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
            _create_kernel_binding_data(agent_id=agent_id, image="image-1", image_id=_IMAGE_ID_1),
            _create_kernel_binding_data(agent_id=agent_id, image="image-2", image_id=_IMAGE_ID_2),
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
    network_id: str | None = None,
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
        network_id=network_id,
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
def session_for_start_persistent_network() -> SessionDataForStart:
    """Multi-node session attached to a pre-created persistent network."""
    return _create_session_for_start(
        kernels=[
            _create_kernel_binding_data(agent_id=AgentId("agent-1"), cluster_idx=0),
            _create_kernel_binding_data(agent_id=AgentId("agent-2"), cluster_idx=1),
        ],
        cluster_mode=ClusterMode.MULTI_NODE,
        network_type=NetworkType.PERSISTENT,
        network_id=str(_PERSISTENT_NETWORK_ID),
    )


@pytest.fixture
def session_for_start_persistent_network_unset() -> SessionDataForStart:
    """Session declaring a persistent network without naming one."""
    return _create_session_for_start(
        network_type=NetworkType.PERSISTENT,
        network_id=None,
    )


@pytest.fixture
def session_for_start_kernel_no_agent() -> SessionDataForStart:
    """Session with kernel that has no agent assigned."""
    kernel = _create_kernel_binding_data()
    kernel.agent_id = None
    return _create_session_for_start(kernels=[kernel])


# =============================================================================
# Image Config Fixtures
# =============================================================================


def _create_image_config_data(
    canonical: str = "cr.backend.ai/stable/python:3.9-ubuntu20.04",
    image_id: UUID = _DEFAULT_IMAGE_ID,
) -> ImageConfigData:
    """Create ImageConfigData for tests."""
    return ImageConfigData(
        id=image_id,
        canonical=canonical,
        architecture=ArchName("x86_64"),
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
def image_config_default() -> dict[UUID, ImageConfigData]:
    """Default image configuration."""
    config = _create_image_config_data()
    return {
        config.id: config,
    }


@pytest.fixture
def image_configs_multiple() -> dict[UUID, ImageConfigData]:
    """Multiple image configurations."""
    config1 = _create_image_config_data(canonical="image-1", image_id=_IMAGE_ID_1)
    config2 = _create_image_config_data(canonical="image-2", image_id=_IMAGE_ID_2)
    return {
        config1.id: config1,
        config2.id: config2,
    }
