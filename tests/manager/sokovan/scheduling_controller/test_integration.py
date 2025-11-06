"""Integration tests for the complete scheduling controller flow."""

import uuid
from datetime import datetime, timedelta
from pathlib import PurePosixPath
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from dateutil.tz import tzutc

from ai.backend.common.plugin.hook import HookResult, HookResults
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelEnqueueingConfig,
    MountPermission,
    SessionId,
    SessionTypes,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    ContainerUserInfo,
    ImageInfo,
    ScalingGroupNetworkInfo,
    SessionCreationContext,
    SessionCreationSpec,
    SessionEnqueueData,
)
from ai.backend.manager.sokovan.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)
from ai.backend.manager.types import UserScope


@pytest.fixture
async def mock_repository():
    """Create a mock repository."""
    repo = AsyncMock()
    repo.enqueue_session = AsyncMock(return_value=SessionId(uuid.uuid4()))
    repo.query_allowed_scaling_groups = AsyncMock(
        return_value=[
            AllowedScalingGroup(
                name="default", is_private=False, scheduler_opts=ScalingGroupOpts()
            ),
            AllowedScalingGroup(name="gpu", is_private=False, scheduler_opts=ScalingGroupOpts()),
            AllowedScalingGroup(name="private", is_private=True, scheduler_opts=ScalingGroupOpts()),
        ]
    )
    repo.fetch_session_creation_data = AsyncMock()
    return repo


@pytest.fixture
async def mock_config_provider():
    """Create a mock config provider."""
    provider = MagicMock()
    provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(
        return_value=["user", "group", "system"]
    )
    provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
        return_value={"cpu": "count", "mem": "bytes", "cuda.shares": "count"}
    )
    return provider


@pytest.fixture
async def scheduling_controller(
    mock_repository,
    mock_config_provider,
):
    """Create a SchedulingController instance with mocks."""
    hook_result = HookResult(status=HookResults.PASSED)
    hook_plugin_ctx = AsyncMock()
    hook_plugin_ctx.notify = AsyncMock(return_value=hook_result)
    hook_plugin_ctx.dispatch = AsyncMock(return_value=hook_result)
    args = SchedulingControllerArgs(
        repository=mock_repository,
        config_provider=mock_config_provider,
        storage_manager=AsyncMock(),
        event_producer=AsyncMock(),
        valkey_schedule=AsyncMock(),
        network_plugin_ctx=AsyncMock(),
        hook_plugin_ctx=hook_plugin_ctx,
    )
    return SchedulingController(args)


class TestSingleKernelSession:
    """Test cases for single kernel sessions."""

    async def test_basic_single_kernel_session(
        self, scheduling_controller, mock_repository
    ) -> None:
        """Test creating a basic single kernel session."""
        spec = SessionCreationSpec(
            session_creation_id="test-001",
            session_name="single-kernel-test",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="user",
            ),
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            priority=10,
            resource_policy={
                "max_containers_per_session": 5,
            },
            kernel_specs=[
                cast(
                    KernelEnqueueingConfig,
                    {
                        "image_ref": MagicMock(canonical="python:3.9"),
                        "resources": {"cpu": "2", "mem": "4g"},
                    },
                )
            ],
            creation_spec={
                "mounts": ["home"],
                "environ": {"TEST_VAR": "test_value"},
            },
        )

        # Setup mock context
        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
            allowed_scaling_groups=[
                AllowedScalingGroup(
                    name="default", is_private=False, scheduler_opts=ScalingGroupOpts()
                )
            ],
            image_infos={
                "python:3.9": ImageInfo(
                    canonical="python:3.9",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={},
                    resource_spec={
                        "cpu": {"min": "1", "max": "16"},
                        "mem": {"min": "1g", "max": "32g"},
                    },
                )
            },
            vfolder_mounts=[
                VFolderMount(
                    name="home",
                    vfid=VFolderID(quota_scope_id=None, folder_id=uuid.uuid4()),
                    vfsubpath=PurePosixPath("."),
                    host_path=PurePosixPath("/data/vfolders/home"),
                    kernel_path=PurePosixPath("/home/work"),
                    mount_perm=MountPermission.READ_WRITE,
                    usage_mode=VFolderUsageMode.GENERAL,
                )
            ],
            dotfile_data={"bashrc": "export PS1='$ '"},
            container_user_info=ContainerUserInfo(
                uid=1000,
                main_gid=1000,
                supplementary_gids=[100, 200],
            ),
        )

        # Execute
        await scheduling_controller.enqueue_session(spec)

        # Verify
        mock_repository.enqueue_session.assert_called_once()

        # Check the session data passed to repository
        session_data = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.name == "single-kernel-test"
        assert session_data.cluster_size == 1
        assert len(session_data.kernels) == 1
        assert session_data.kernels[0].cluster_role == "main"
        assert session_data.kernels[0].uid == 1000
        assert session_data.kernels[0].main_gid == 1000
        assert session_data.kernels[0].gids == [100, 200]


class TestMultiContainerSession:
    """Test cases for multi-container sessions."""

    async def test_multi_container_replication(
        self, scheduling_controller, mock_repository
    ) -> None:
        """Test multi-container session with single spec replication."""
        spec = SessionCreationSpec(
            session_creation_id="test-002",
            session_name="multi-container-test",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="user",
            ),
            session_type=SessionTypes.BATCH,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=4,
            priority=10,
            resource_policy={
                "max_containers_per_session": 10,
            },
            kernel_specs=[
                cast(
                    KernelEnqueueingConfig,
                    {
                        "image_ref": MagicMock(canonical="tensorflow:2.0"),
                        "resources": {"cpu": "4", "mem": "8g", "cuda.shares": "0.5"},
                    },
                )
            ],
            creation_spec={
                "preopen_ports": [7007, 7008],  # Custom ports (not overlapping with services)
            },
            starts_at=datetime.now(tzutc()) + timedelta(hours=1),
            batch_timeout=timedelta(minutes=30),
        )

        # Setup mock context
        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
            allowed_scaling_groups=[
                AllowedScalingGroup(name="gpu", is_private=False, scheduler_opts=ScalingGroupOpts())
            ],
            image_infos={
                "tensorflow:2.0": ImageInfo(
                    canonical="tensorflow:2.0",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={
                        "ai.backend.service-ports": "tensorboard:http:6006",
                    },
                    resource_spec={
                        "cpu": {"min": "1", "max": "16"},
                        "mem": {"min": "2g", "max": "64g"},
                        "cuda.shares": {"min": "0", "max": "4"},  # Allow 0 as minimum for testing
                    },
                )
            },
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        # Execute
        await scheduling_controller.enqueue_session(spec)

        # Verify
        session_data = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.cluster_size == 4
        assert len(session_data.kernels) == 4

        # Check main kernel
        assert session_data.kernels[0].cluster_role == "main"
        assert session_data.kernels[0].cluster_idx == 1
        assert session_data.kernels[0].local_rank == 0
        assert session_data.kernels[0].cluster_hostname == "main1"

        # Check sub kernels
        for i in range(1, 4):
            assert session_data.kernels[i].cluster_role == "sub"
            assert session_data.kernels[i].cluster_idx == i
            assert session_data.kernels[i].local_rank == i
            assert session_data.kernels[i].cluster_hostname == f"sub{i}"

        # Check batch session specific fields
        assert session_data.starts_at is not None
        assert session_data.batch_timeout == 30 * 60  # 30 minutes in seconds

    async def test_multi_container_different_images(
        self, scheduling_controller, mock_repository
    ) -> None:
        """Test multi-container session with different images per kernel."""
        spec = SessionCreationSpec(
            session_creation_id="test-003",
            session_name="heterogeneous-cluster",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="admin",
            ),
            session_type=SessionTypes.INFERENCE,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=3,
            priority=20,
            resource_policy={
                "max_containers_per_session": 10,
            },
            kernel_specs=cast(
                list[KernelEnqueueingConfig],
                [
                    {
                        "image_ref": MagicMock(canonical="nginx:latest"),
                        "resources": {"cpu": "2", "mem": "2g"},
                        "cluster_role": "main",
                    },
                    {
                        "image_ref": MagicMock(canonical="python:3.9"),
                        "resources": {"cpu": "4", "mem": "8g"},
                        "cluster_role": "worker",
                    },
                    {
                        "image_ref": MagicMock(canonical="redis:6"),
                        "resources": {"cpu": "1", "mem": "1g"},
                        "cluster_role": "cache",
                    },
                ],
            ),
            creation_spec={},
        )

        # Setup mock context with multiple images
        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(use_host_network=True),
            allowed_scaling_groups=[
                AllowedScalingGroup(
                    name="default", is_private=False, scheduler_opts=ScalingGroupOpts()
                )
            ],
            image_infos={
                "nginx:latest": ImageInfo(
                    canonical="nginx:latest",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={},
                    resource_spec={
                        "cpu": {"min": "0.5", "max": "8"},
                        "mem": {"min": "512m", "max": "16g"},
                    },
                ),
                "python:3.9": ImageInfo(
                    canonical="python:3.9",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={},
                    resource_spec={
                        "cpu": {"min": "1", "max": "16"},
                        "mem": {"min": "1g", "max": "32g"},
                    },
                ),
                "redis:6": ImageInfo(
                    canonical="redis:6",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={},
                    resource_spec={
                        "cpu": {"min": "0.5", "max": "4"},
                        "mem": {"min": "256m", "max": "8g"},
                    },
                ),
            },
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        # Execute
        await scheduling_controller.enqueue_session(spec)

        # Verify
        session_data = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.cluster_size == 3
        assert len(session_data.kernels) == 3
        assert session_data.network_type == NetworkType.HOST

        # Check each kernel has correct image and role
        assert session_data.kernels[0].image == "nginx:latest"
        assert session_data.kernels[0].cluster_role == "main"

        assert session_data.kernels[1].image == "python:3.9"
        assert session_data.kernels[1].cluster_role == "worker"

        assert session_data.kernels[2].image == "redis:6"
        assert session_data.kernels[2].cluster_role == "cache"


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    async def test_agent_preassignment(self, scheduling_controller, mock_repository) -> None:
        """Test session with pre-assigned agents."""
        spec = SessionCreationSpec(
            session_creation_id="test-preassigned",
            session_name="preassigned-agents",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="superadmin",
            ),
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=3,
            priority=30,
            resource_policy={"max_containers_per_session": 10},
            kernel_specs=cast(
                list[KernelEnqueueingConfig],
                [
                    {"image_ref": MagicMock(canonical="python:3.9")},
                    {"image_ref": MagicMock(canonical="python:3.9")},
                    {"image_ref": MagicMock(canonical="python:3.9")},
                ],
            ),
            creation_spec={},
            designated_agent_list=["agent-001", "agent-002", "agent-003"],
        )

        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
            allowed_scaling_groups=[
                AllowedScalingGroup(
                    name="default", is_private=False, scheduler_opts=ScalingGroupOpts()
                )
            ],
            image_infos={
                "python:3.9": ImageInfo(
                    canonical="python:3.9",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={},
                    resource_spec={
                        "cpu": {"min": "1", "max": "16"},
                        "mem": {"min": "1g", "max": "32g"},
                    },
                )
            },
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        # Execute
        await scheduling_controller.enqueue_session(spec)

        # Verify agents are correctly assigned
        session_data: SessionEnqueueData = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.designated_agent_list == [
            "agent-001",
            "agent-002",
            "agent-003",
        ]

    async def test_network_types(self, scheduling_controller, mock_repository) -> None:
        """Test different network type configurations."""
        # Test VOLATILE network (default)
        spec_volatile = SessionCreationSpec(
            session_creation_id="test-net-volatile",
            session_name="volatile-network",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="user",
            ),
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=2,
            priority=10,
            resource_policy={"max_containers_per_session": 5},
            kernel_specs=[
                cast(KernelEnqueueingConfig, {"image_ref": MagicMock(canonical="python:3.9")}),
            ],
            creation_spec={},
            network=None,  # No persistent network
        )

        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(
                use_host_network=False  # Not using host network
            ),
            allowed_scaling_groups=[
                AllowedScalingGroup(
                    name="default", is_private=False, scheduler_opts=ScalingGroupOpts()
                )
            ],
            image_infos={
                "python:3.9": ImageInfo(
                    canonical="python:3.9",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={},
                    resource_spec={
                        "cpu": {"min": "1", "max": "16"},
                        "mem": {"min": "1g", "max": "32g"},
                    },
                )
            },
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        await scheduling_controller.enqueue_session(spec_volatile)
        session_data = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.network_type == NetworkType.VOLATILE

        # Test HOST network
        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(
                use_host_network=True  # Using host network
            ),
            allowed_scaling_groups=[
                AllowedScalingGroup(
                    name="default", is_private=False, scheduler_opts=ScalingGroupOpts()
                )
            ],
            image_infos={
                "python:3.9": ImageInfo(
                    canonical="python:3.9",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={},
                    resource_spec={
                        "cpu": {"min": "1", "max": "16"},
                        "mem": {"min": "1g", "max": "32g"},
                    },
                )
            },
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        spec_host = SessionCreationSpec(
            session_creation_id="test-net-host",
            session_name="host-network",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="user",
            ),
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            priority=10,
            resource_policy={"max_containers_per_session": 5},
            kernel_specs=[
                cast(KernelEnqueueingConfig, {"image_ref": MagicMock(canonical="python:3.9")})
            ],
            creation_spec={},
        )

        await scheduling_controller.enqueue_session(spec_host)
        session_data = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.network_type == NetworkType.HOST

    async def test_session_dependencies(self, scheduling_controller, mock_repository) -> None:
        """Test session with dependencies."""
        dependency_ids = [SessionId(uuid.uuid4()) for _ in range(3)]

        spec = SessionCreationSpec(
            session_creation_id="test-deps",
            session_name="dependent-session",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="user",
            ),
            session_type=SessionTypes.BATCH,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            priority=5,
            resource_policy={},
            kernel_specs=[
                cast(KernelEnqueueingConfig, {"image_ref": MagicMock(canonical="python:3.9")}),
            ],
            creation_spec={},
            dependency_sessions=dependency_ids,
        )

        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
            allowed_scaling_groups=[
                AllowedScalingGroup(
                    name="default", is_private=False, scheduler_opts=ScalingGroupOpts()
                )
            ],
            image_infos={
                "python:3.9": ImageInfo(
                    canonical="python:3.9",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={},
                    resource_spec={
                        "cpu": {"min": "1", "max": "16"},
                        "mem": {"min": "1g", "max": "32g"},
                    },
                )
            },
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        await scheduling_controller.enqueue_session(spec)

        session_data = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.dependencies == dependency_ids


class TestMultiClusterScenarios:
    """Test cases for multi-cluster (MULTI_NODE) scenarios."""

    async def test_multi_cluster_single_kernel_replication(
        self, scheduling_controller, mock_repository
    ) -> None:
        """Test MULTI_NODE cluster with single kernel spec being replicated across nodes."""
        spec = SessionCreationSpec(
            session_creation_id="test-mc-001",
            session_name="multi-cluster-replicated",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="user",
            ),
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=4,
            priority=15,
            resource_policy={"max_containers_per_session": 10},
            kernel_specs=[
                cast(
                    KernelEnqueueingConfig,
                    {
                        "image_ref": MagicMock(canonical="pytorch:2.0"),
                        "resources": {"cpu": "8", "mem": "16g", "cuda.shares": "1"},
                    },
                )
            ],  # Single spec to be replicated
            creation_spec={
                "mounts": ["datasets", "checkpoints"],
                "environ": {"DISTRIBUTED": "true"},
            },
        )

        # Setup mock context
        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
            allowed_scaling_groups=[
                AllowedScalingGroup(
                    name="gpu-cluster", is_private=False, scheduler_opts=ScalingGroupOpts()
                )
            ],
            image_infos={
                "pytorch:2.0": ImageInfo(
                    canonical="pytorch:2.0",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={
                        "ai.backend.service-ports": "tensorboard:http:6006,jupyter:http:8888",
                    },
                    resource_spec={
                        "cpu": {"min": "2", "max": "32"},
                        "mem": {"min": "4g", "max": "128g"},
                        "cuda.shares": {"min": "0", "max": "8"},
                    },
                )
            },
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(
                uid=2000,
                main_gid=2000,
                supplementary_gids=[2001, 2002],
            ),
        )

        # Execute
        await scheduling_controller.enqueue_session(spec)

        # Verify
        session_data = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.cluster_size == 4
        assert len(session_data.kernels) == 4

        # All kernels should have the same image
        for kernel in session_data.kernels:
            assert kernel.image == "pytorch:2.0"
            assert kernel.uid == 2000
            assert kernel.main_gid == 2000
            assert kernel.gids == [2001, 2002]

        # Check cluster configuration
        assert session_data.kernels[0].cluster_role == "main"
        assert session_data.kernels[0].cluster_idx == 1
        assert session_data.kernels[0].local_rank == 0
        assert session_data.kernels[0].cluster_hostname == "main1"

        for i in range(1, 4):
            assert session_data.kernels[i].cluster_role == "sub"
            assert session_data.kernels[i].cluster_idx == i
            assert session_data.kernels[i].local_rank == i
            assert session_data.kernels[i].cluster_hostname == f"sub{i}"

    async def test_multi_cluster_heterogeneous_config(
        self, scheduling_controller, mock_repository
    ) -> None:
        """Test MULTI_NODE cluster with different configurations per node."""
        spec = SessionCreationSpec(
            session_creation_id="test-mc-002",
            session_name="heterogeneous-multi-cluster",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="research",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="researcher",
            ),
            session_type=SessionTypes.BATCH,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=5,
            priority=25,
            resource_policy={"max_containers_per_session": 10},
            kernel_specs=cast(
                list[KernelEnqueueingConfig],
                [
                    {
                        "image_ref": MagicMock(canonical="spark:master"),
                        "resources": {"cpu": "16", "mem": "64g"},
                        "cluster_role": "main",
                    },
                    {
                        "image_ref": MagicMock(canonical="spark:worker"),
                        "resources": {"cpu": "8", "mem": "32g"},
                        "cluster_role": "worker",
                    },
                    {
                        "image_ref": MagicMock(canonical="spark:worker"),
                        "resources": {"cpu": "8", "mem": "32g"},
                        "cluster_role": "worker",
                    },
                    {
                        "image_ref": MagicMock(canonical="spark:worker"),
                        "resources": {"cpu": "8", "mem": "32g"},
                        "cluster_role": "worker",
                    },
                    {
                        "image_ref": MagicMock(canonical="jupyter:notebook"),
                        "resources": {"cpu": "4", "mem": "16g"},
                        "cluster_role": "notebook",
                    },
                ],
            ),
            creation_spec={
                "scaling_group": "gpu-cluster",
            },
            starts_at=datetime.now(tzutc()) + timedelta(minutes=5),
            batch_timeout=timedelta(hours=2),
        )

        # Setup mock context with multiple images
        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
            allowed_scaling_groups=[
                AllowedScalingGroup(
                    name="gpu-cluster", is_private=False, scheduler_opts=ScalingGroupOpts()
                )
            ],
            image_infos={
                "spark:master": ImageInfo(
                    canonical="spark:master",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={
                        "ai.backend.service-ports": "spark-ui:http:8080,spark-master:tcp:7077",
                    },
                    resource_spec={
                        "cpu": {"min": "4", "max": "32"},
                        "mem": {"min": "8g", "max": "128g"},
                    },
                ),
                "spark:worker": ImageInfo(
                    canonical="spark:worker",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={
                        "ai.backend.service-ports": "spark-worker:http:8081",
                    },
                    resource_spec={
                        "cpu": {"min": "2", "max": "16"},
                        "mem": {"min": "4g", "max": "64g"},
                    },
                ),
                "jupyter:notebook": ImageInfo(
                    canonical="jupyter:notebook",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={
                        "ai.backend.service-ports": "jupyter:http:8888",
                    },
                    resource_spec={
                        "cpu": {"min": "1", "max": "8"},
                        "mem": {"min": "2g", "max": "32g"},
                    },
                ),
            },
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        # Execute
        await scheduling_controller.enqueue_session(spec)

        # Verify
        session_data = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.cluster_size == 5
        assert len(session_data.kernels) == 5

        # Check each kernel configuration
        assert session_data.kernels[0].image == "spark:master"
        assert session_data.kernels[0].cluster_role == "main"

        for i in range(1, 4):
            assert session_data.kernels[i].image == "spark:worker"
            assert session_data.kernels[i].cluster_role == "worker"

        assert session_data.kernels[4].image == "jupyter:notebook"
        assert session_data.kernels[4].cluster_role == "notebook"

        # Check batch session specific fields
        assert session_data.starts_at is not None
        assert session_data.batch_timeout == 2 * 60 * 60  # 2 hours in seconds

    async def test_multi_cluster_with_agent_assignment(
        self, scheduling_controller, mock_repository
    ) -> None:
        """Test MULTI_NODE cluster with pre-assigned agents for each node."""
        spec = SessionCreationSpec(
            session_creation_id="test-mc-003",
            session_name="multi-cluster-assigned",
            access_key=AccessKey("test-access-key"),
            user_scope=UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="admin",
            ),
            session_type=SessionTypes.INFERENCE,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=3,
            priority=50,
            resource_policy={"max_containers_per_session": 10},
            kernel_specs=[
                cast(
                    KernelEnqueueingConfig,
                    {
                        "image_ref": MagicMock(canonical="llm:server"),
                        "resources": {"cpu": "8", "mem": "32g", "cuda.shares": "2"},
                    },
                ),
            ],  # Single spec to replicate with resources
            creation_spec={
                "scaling_group": "inference-cluster",
            },
            designated_agent_list=["gpu-agent-01", "gpu-agent-02", "gpu-agent-03"],
        )

        mock_repository.fetch_session_creation_data.return_value = SessionCreationContext(
            scaling_group_network=ScalingGroupNetworkInfo(
                use_host_network=True
            ),  # Using host network
            allowed_scaling_groups=[
                AllowedScalingGroup(
                    name="inference-cluster", is_private=False, scheduler_opts=ScalingGroupOpts()
                )
            ],
            image_infos={
                "llm:server": ImageInfo(
                    canonical="llm:server",
                    architecture="x86_64",
                    registry="docker.io",
                    labels={
                        "ai.backend.service-ports": "api:http:8000,metrics:http:9090",
                    },
                    resource_spec={
                        "cpu": {"min": "4", "max": "32"},
                        "mem": {"min": "16g", "max": "256g"},
                        "cuda.shares": {"min": "0", "max": "8"},  # Allow 0 for testing
                    },
                )
            },
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

        # Execute
        await scheduling_controller.enqueue_session(spec)

        # Verify
        session_data: SessionEnqueueData = mock_repository.enqueue_session.call_args[0][0]
        assert session_data.cluster_size == 3
        assert len(session_data.kernels) == 3
        assert session_data.network_type == NetworkType.HOST  # Should use host network
        assert session_data.designated_agent_list == [
            "gpu-agent-01",
            "gpu-agent-02",
            "gpu-agent-03",
        ]

        # All should have same image
        for kernel in session_data.kernels:
            assert kernel.image == "llm:server"
