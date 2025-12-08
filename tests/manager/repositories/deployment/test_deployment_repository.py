"""Tests for DeploymentRepository."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    BinarySize,
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
    ServicePort,
    ServicePortProtocols,
    SessionId,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models import KeyPairResourcePolicyRow, KeyPairRow
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.kernel import KernelRow, KernelStatus
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import (
    SessionResult,
    SessionRow,
    SessionStatus,
    SessionTypes,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.deployment import DeploymentRepository


def create_test_password_info(password: str) -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestDeploymentRepositoryFetchRouteServiceDiscoveryInfo:
    """Test cases for fetch_route_service_discovery_info method."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans deployment data after each test."""
        yield database_engine

        # Cleanup in reverse dependency order
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(RoutingRow))
            await db_sess.execute(sa.delete(EndpointRow))
            await db_sess.execute(sa.delete(KernelRow))
            await db_sess.execute(sa.delete(SessionRow))
            await db_sess.execute(sa.delete(KeyPairRow))
            await db_sess.execute(sa.delete(GroupRow))
            await db_sess.execute(sa.delete(UserRow))
            await db_sess.execute(sa.delete(KeyPairResourcePolicyRow))
            await db_sess.execute(sa.delete(ProjectResourcePolicyRow))
            await db_sess.execute(sa.delete(UserResourcePolicyRow))
            await db_sess.execute(sa.delete(AgentRow))
            await db_sess.execute(sa.delete(ScalingGroupRow))
            await db_sess.execute(sa.delete(DomainRow))

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for deployment",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return name."""
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sgroup)
            await db_sess.flush()

        yield sgroup_name

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[AgentId, None]:
        """Create test agent and return agent ID."""
        agent_id = AgentId(f"i-{uuid.uuid4().hex[:12]}")

        async with db_with_cleanup.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(tzutc()),
                region="local",
                scaling_group=test_scaling_group_name,
                schedulable=True,
                available_slots=ResourceSlot({"cpu": Decimal("8.0"), "mem": Decimal("16384")}),
                occupied_slots=ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
                addr="127.0.0.1:2001",
                architecture="x86_64",
                version="24.03.0",
            )
            db_sess.add(agent)
            await db_sess.flush()

        yield agent_id

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test keypair resource policy and return policy name."""
        policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("100"),
                    "mem": Decimal("102400"),
                }),
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=2,
                max_pending_session_count=5,
                max_pending_session_resource_slots=ResourceSlot({
                    "cpu": Decimal("50"),
                    "mem": Decimal("51200"),
                }),
                max_containers_per_session=10,
                idle_timeout=3600,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test user and return user UUID."""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=create_test_password_info("test_password"),
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test project resource policy and return policy name."""
        policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                max_network_count=5,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test group and return group ID."""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain_name,
                resource_policy=test_project_resource_policy_name,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_id

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        """Create test keypair and return access key."""
        access_key = AccessKey(f"AKIATEST{uuid.uuid4().hex[:12].upper()}")

        async with db_with_cleanup.begin_session() as db_sess:
            # Get user email for user_id field
            user_result = await db_sess.execute(
                sa.select(UserRow.email).where(UserRow.uuid == test_user_uuid)
            )
            user_email = user_result.scalar_one()

            keypair = KeyPairRow(
                access_key=access_key,
                secret_key="dummy-secret",
                user_id=user_email,
                user=test_user_uuid,
                is_active=True,
                resource_policy=test_keypair_resource_policy_name,
            )
            db_sess.add(keypair)
            await db_sess.flush()

        yield access_key

    @pytest.fixture
    async def test_session_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
        test_domain_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> AsyncGenerator[SessionId, None]:
        """Create test session and return session ID."""
        session_id = SessionId(uuid.uuid4())

        async with db_with_cleanup.begin_session() as db_sess:
            session = SessionRow(
                id=session_id,
                name=f"test-session-{uuid.uuid4().hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
                scaling_group_name=test_scaling_group_name,
                status=SessionStatus.RUNNING,
                cluster_mode=ClusterMode.SINGLE_NODE,
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                created_at=datetime.now(tzutc()),
                images=["python:3.11"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
            )
            db_sess.add(session)
            await db_sess.flush()

        yield session_id

    @pytest.fixture
    async def test_kernel_with_inference_port(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
        test_agent_id: AgentId,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> AsyncGenerator[tuple[uuid.UUID, str, int], None]:
        """Create test kernel with inference port and return (kernel_id, host, port)."""
        kernel_id = uuid.uuid4()
        kernel_host = "10.0.1.5"
        inference_port = 8080

        service_ports: list[ServicePort] = [
            {
                "name": "inference",
                "protocol": ServicePortProtocols("http"),
                "container_ports": [8080],
                "host_ports": [inference_port],
                "is_inference": True,
            }
        ]

        async with db_with_cleanup.begin_session() as db_sess:
            kernel = KernelRow(
                id=kernel_id,
                session_id=test_session_id,
                access_key=test_access_key,
                agent=test_agent_id,
                agent_addr="127.0.0.1:2001",
                scaling_group=test_scaling_group_name,
                cluster_role="main",
                cluster_idx=1,
                cluster_hostname=f"kernel-{kernel_id.hex[:8]}",
                image="python:3.11",
                architecture="x86_64",
                registry="docker.io",
                status=KernelStatus.RUNNING,
                status_changed=datetime.now(tzutc()),
                kernel_host=kernel_host,
                service_ports=service_ports,
                occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                mounts=[],
                environ={},
                vfolder_mounts=[],
                preopen_ports=[],
                repl_in_port=2001,
                repl_out_port=2002,
                stdin_port=2003,
                stdout_port=2004,
            )
            db_sess.add(kernel)
            await db_sess.flush()

        yield (kernel_id, kernel_host, inference_port)

    @pytest.fixture
    async def test_kernel_without_inference_port(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_session_id: SessionId,
        test_agent_id: AgentId,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test kernel without inference port and return kernel_id."""
        kernel_id = uuid.uuid4()

        service_ports: list[ServicePort] = [
            {
                "name": "ssh",
                "protocol": ServicePortProtocols("tcp"),
                "container_ports": [22],
                "host_ports": [2200],
                "is_inference": False,
            }
        ]

        async with db_with_cleanup.begin_session() as db_sess:
            kernel = KernelRow(
                id=kernel_id,
                session_id=test_session_id,
                access_key=test_access_key,
                agent=test_agent_id,
                agent_addr="127.0.0.1:2001",
                scaling_group=test_scaling_group_name,
                cluster_role="main",
                cluster_idx=1,
                cluster_hostname=f"kernel-{kernel_id.hex[:8]}",
                image="python:3.11",
                architecture="x86_64",
                registry="docker.io",
                status=KernelStatus.RUNNING,
                status_changed=datetime.now(tzutc()),
                kernel_host="10.0.1.6",
                service_ports=service_ports,
                occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                mounts=[],
                environ={},
                vfolder_mounts=[],
                preopen_ports=[],
                repl_in_port=2001,
                repl_out_port=2002,
                stdin_port=2003,
                stdout_port=2004,
            )
            db_sess.add(kernel)
            await db_sess.flush()

        yield kernel_id

    @pytest.fixture
    async def test_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test endpoint and return endpoint ID."""
        endpoint_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            endpoint = EndpointRow(
                id=endpoint_id,
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=test_user_uuid,
                session_owner=test_user_uuid,
                domain=test_domain_name,
                project=test_group_id,
                resource_group=test_scaling_group_name,
                model=None,  # Optional field
                desired_replicas=1,
                image=None,  # Set to None since we're in DESTROYED state
                runtime_variant=RuntimeVariant.VLLM,
                url="http://test.example.com",
                open_to_public=False,
                lifecycle_stage=EndpointLifecycle.DESTROYED,  # DESTROYED allows null image
                resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
            )
            db_sess.add(endpoint)
            await db_sess.flush()

        yield endpoint_id

    @pytest.fixture
    async def test_route_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_session_id: SessionId,
        test_domain_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test route and return route ID."""
        route_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            route = RoutingRow(
                id=route_id,
                endpoint=test_endpoint_id,
                session=test_session_id,
                session_owner=test_user_uuid,
                domain=test_domain_name,
                project=test_group_id,
                traffic_ratio=1.0,
            )
            db_sess.add(route)
            await db_sess.flush()

        yield route_id

    @pytest.fixture
    async def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[DeploymentRepository, None]:
        """Create DeploymentRepository instance with database and mocked dependencies."""
        # Create mock dependencies
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        repo = DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )
        yield repo

    @pytest.mark.asyncio
    async def test_fetch_single_route_with_inference_port(
        self,
        deployment_repository: DeploymentRepository,
        test_route_id: uuid.UUID,
        test_endpoint_id: uuid.UUID,
        test_kernel_with_inference_port: tuple[uuid.UUID, str, int],
    ) -> None:
        """Test fetching service discovery info for a single route with inference port."""
        kernel_id, kernel_host, inference_port = test_kernel_with_inference_port

        result = await deployment_repository.fetch_route_service_discovery_info({test_route_id})

        assert len(result) == 1
        info = result[0]
        assert info.route_id == test_route_id
        assert info.endpoint_id == test_endpoint_id
        assert info.kernel_host == kernel_host
        assert info.kernel_port == inference_port
        assert info.runtime_variant == "vllm"
        assert "test-endpoint" in info.endpoint_name

    @pytest.mark.asyncio
    async def test_fetch_route_without_inference_port(
        self,
        deployment_repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_session_id: SessionId,
        test_domain_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
        test_kernel_without_inference_port: uuid.UUID,
    ) -> None:
        """Test that routes without inference port are excluded from results."""
        route_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            route = RoutingRow(
                id=route_id,
                endpoint=test_endpoint_id,
                session=test_session_id,
                session_owner=test_user_uuid,
                domain=test_domain_name,
                project=test_group_id,
                traffic_ratio=1.0,
            )
            db_sess.add(route)
            await db_sess.flush()

        result = await deployment_repository.fetch_route_service_discovery_info({route_id})

        # Should return empty list because kernel has no inference port
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_empty_route_ids(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Test that empty route_ids set returns empty list immediately."""
        result = await deployment_repository.fetch_route_service_discovery_info(set())

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_nonexistent_route_ids(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Test that nonexistent route IDs return empty list."""
        nonexistent_id = uuid.uuid4()

        result = await deployment_repository.fetch_route_service_discovery_info({nonexistent_id})

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_multiple_routes(
        self,
        deployment_repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_access_key: AccessKey,
        test_agent_id: AgentId,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> None:
        """Test fetching service discovery info for multiple routes."""
        # Create 3 sets of endpoint/session/kernel/route
        route_ids = set()
        endpoint_ids = []

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(3):
                # Create endpoint
                endpoint_id = uuid.uuid4()
                endpoint = EndpointRow(
                    id=endpoint_id,
                    name=f"endpoint-{i}",
                    created_user=test_user_uuid,
                    session_owner=test_user_uuid,
                    domain=test_domain_name,
                    project=test_group_id,
                    resource_group=test_scaling_group_name,
                    model=None,  # Optional field
                    desired_replicas=1,
                    image=None,  # Set to None since we're in DESTROYED state
                    runtime_variant=RuntimeVariant.VLLM,
                    url=f"http://test{i}.example.com",
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.DESTROYED,  # DESTROYED allows null image
                    resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
                )
                db_sess.add(endpoint)
                endpoint_ids.append(endpoint_id)

                # Create session
                session_id = SessionId(uuid.uuid4())
                session = SessionRow(
                    id=session_id,
                    name=f"session-{i}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    access_key=test_access_key,
                    scaling_group_name=test_scaling_group_name,
                    status=SessionStatus.RUNNING,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                    created_at=datetime.now(tzutc()),
                    images=["python:3.11"],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                )
                db_sess.add(session)

                # Create kernel with inference port
                kernel_id = uuid.uuid4()
                service_ports: list[ServicePort] = [
                    {
                        "name": "inference",
                        "protocol": ServicePortProtocols("http"),
                        "container_ports": [8080],
                        "host_ports": [8080 + i],
                        "is_inference": True,
                    }
                ]
                kernel = KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    access_key=test_access_key,
                    agent=test_agent_id,
                    agent_addr="127.0.0.1:2001",
                    scaling_group=test_scaling_group_name,
                    cluster_role="main",
                    cluster_idx=1,
                    cluster_hostname=f"kernel-{i}",
                    image="python:3.11",
                    architecture="x86_64",
                    registry="docker.io",
                    status=KernelStatus.RUNNING,
                    status_changed=datetime.now(tzutc()),
                    kernel_host=f"10.0.1.{10 + i}",
                    service_ports=service_ports,
                    occupied_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                    requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                    domain_name=test_domain_name,
                    group_id=test_group_id,
                    user_uuid=test_user_uuid,
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2001,
                    repl_out_port=2002,
                    stdin_port=2003,
                    stdout_port=2004,
                )
                db_sess.add(kernel)

                # Create route
                route_id = uuid.uuid4()
                route = RoutingRow(
                    id=route_id,
                    endpoint=endpoint_id,
                    session=session_id,
                    session_owner=test_user_uuid,
                    domain=test_domain_name,
                    project=test_group_id,
                    traffic_ratio=1.0,
                )
                db_sess.add(route)
                route_ids.add(route_id)

            await db_sess.flush()

        result = await deployment_repository.fetch_route_service_discovery_info(route_ids)

        # Should return 3 RouteServiceDiscoveryInfo objects
        assert len(result) == 3

        # Verify each result has correct structure
        for info in result:
            assert info.route_id in route_ids
            assert info.endpoint_id in endpoint_ids
            assert info.kernel_host.startswith("10.0.1.")
            assert 8080 <= info.kernel_port <= 8082
            assert info.runtime_variant == RuntimeVariant.VLLM.value
            assert info.endpoint_name.startswith("endpoint-")


class TestGetDefaultArchitectureFromScalingGroup:
    """Test cases for get_default_architecture_from_scaling_group method."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans data after each test."""
        yield database_engine

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(AgentRow))
            await db_sess.execute(sa.delete(ScalingGroupRow))

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return name."""
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sgroup)
            await db_sess.flush()

        yield sgroup_name

    @pytest.fixture
    async def other_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create another scaling group for isolation tests."""
        sgroup_name = f"other-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Other scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sgroup)
            await db_sess.flush()

        yield sgroup_name

    @pytest.fixture
    async def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[DeploymentRepository, None]:
        """Create DeploymentRepository instance."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        repo = DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )
        yield repo

    async def _create_agent(
        self,
        db: ExtendedAsyncSAEngine,
        scaling_group: str,
        architecture: str,
        *,
        status: AgentStatus = AgentStatus.ALIVE,
        schedulable: bool = True,
        suffix: str = "",
    ) -> AgentId:
        """Helper to create an agent with given properties."""
        agent_id = AgentId(f"i-{suffix or uuid.uuid4().hex[:8]}")
        async with db.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=status,
                status_changed=datetime.now(tzutc()),
                region="local",
                scaling_group=scaling_group,
                schedulable=schedulable,
                available_slots=ResourceSlot({"cpu": Decimal("8.0"), "mem": Decimal("16384")}),
                occupied_slots=ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
                addr=f"127.0.0.{hash(agent_id) % 256}:2001",
                architecture=architecture,
                version="24.03.0",
            )
            db_sess.add(agent)
            await db_sess.flush()
        return agent_id

    @pytest.fixture
    async def agents_mixed_architecture(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[list[AgentId], None]:
        """Create 3 x86_64 agents and 2 aarch64 agents."""
        agent_ids: list[AgentId] = []
        for i in range(3):
            agent_id = await self._create_agent(
                db_with_cleanup,
                test_scaling_group_name,
                "x86_64",
                suffix=f"x86-{i}",
            )
            agent_ids.append(agent_id)

        for i in range(2):
            agent_id = await self._create_agent(
                db_with_cleanup,
                test_scaling_group_name,
                "aarch64",
                suffix=f"arm-{i}",
            )
            agent_ids.append(agent_id)

        yield agent_ids

    @pytest.fixture
    async def single_aarch64_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[AgentId, None]:
        """Create a single aarch64 agent."""
        agent_id = await self._create_agent(
            db_with_cleanup,
            test_scaling_group_name,
            "aarch64",
            suffix="single",
        )
        yield agent_id

    @pytest.fixture
    async def alive_x86_and_lost_aarch64_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[list[AgentId], None]:
        """Create 1 ALIVE x86_64 agent and 3 LOST aarch64 agents."""
        agent_ids: list[AgentId] = []

        agent_id = await self._create_agent(
            db_with_cleanup,
            test_scaling_group_name,
            "x86_64",
            status=AgentStatus.ALIVE,
            suffix="alive",
        )
        agent_ids.append(agent_id)

        for i in range(3):
            agent_id = await self._create_agent(
                db_with_cleanup,
                test_scaling_group_name,
                "aarch64",
                status=AgentStatus.LOST,
                suffix=f"lost-{i}",
            )
            agent_ids.append(agent_id)

        yield agent_ids

    @pytest.fixture
    async def schedulable_x86_and_non_schedulable_aarch64_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[list[AgentId], None]:
        """Create 1 schedulable x86_64 agent and 3 non-schedulable aarch64 agents."""
        agent_ids: list[AgentId] = []

        agent_id = await self._create_agent(
            db_with_cleanup,
            test_scaling_group_name,
            "x86_64",
            schedulable=True,
            suffix="sched",
        )
        agent_ids.append(agent_id)

        for i in range(3):
            agent_id = await self._create_agent(
                db_with_cleanup,
                test_scaling_group_name,
                "aarch64",
                schedulable=False,
                suffix=f"nonsched-{i}",
            )
            agent_ids.append(agent_id)

        yield agent_ids

    @pytest.fixture
    async def agents_in_different_scaling_groups(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
        other_scaling_group_name: str,
    ) -> AsyncGenerator[list[AgentId], None]:
        """Create 1 agent in target group and 3 agents in other group."""
        agent_ids: list[AgentId] = []

        agent_id = await self._create_agent(
            db_with_cleanup,
            test_scaling_group_name,
            "x86_64",
            suffix="target",
        )
        agent_ids.append(agent_id)

        for i in range(3):
            agent_id = await self._create_agent(
                db_with_cleanup,
                other_scaling_group_name,
                "aarch64",
                suffix=f"other-{i}",
            )
            agent_ids.append(agent_id)

        yield agent_ids

    @pytest.mark.asyncio
    async def test_returns_most_common_architecture(
        self,
        deployment_repository: DeploymentRepository,
        test_scaling_group_name: str,
        agents_mixed_architecture: list[AgentId],
    ) -> None:
        """Test that the most common architecture among active agents is returned."""
        result = await deployment_repository.get_default_architecture_from_scaling_group(
            test_scaling_group_name
        )

        # x86_64 is most common (3 vs 2)
        assert result == "x86_64"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_agents(
        self,
        deployment_repository: DeploymentRepository,
        test_scaling_group_name: str,
    ) -> None:
        """Test that None is returned when no active agents exist."""
        result = await deployment_repository.get_default_architecture_from_scaling_group(
            test_scaling_group_name
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_single_architecture(
        self,
        deployment_repository: DeploymentRepository,
        test_scaling_group_name: str,
        single_aarch64_agent: AgentId,
    ) -> None:
        """Test that single agent's architecture is returned correctly."""
        result = await deployment_repository.get_default_architecture_from_scaling_group(
            test_scaling_group_name
        )

        assert result == "aarch64"

    @pytest.mark.asyncio
    async def test_excludes_non_alive_agents(
        self,
        deployment_repository: DeploymentRepository,
        test_scaling_group_name: str,
        alive_x86_and_lost_aarch64_agents: list[AgentId],
    ) -> None:
        """Test that non-ALIVE agents are excluded from consideration."""
        result = await deployment_repository.get_default_architecture_from_scaling_group(
            test_scaling_group_name
        )

        # Only ALIVE agent's architecture should be considered
        assert result == "x86_64"

    @pytest.mark.asyncio
    async def test_excludes_non_schedulable_agents(
        self,
        deployment_repository: DeploymentRepository,
        test_scaling_group_name: str,
        schedulable_x86_and_non_schedulable_aarch64_agents: list[AgentId],
    ) -> None:
        """Test that non-schedulable agents are excluded from consideration."""
        result = await deployment_repository.get_default_architecture_from_scaling_group(
            test_scaling_group_name
        )

        # Only schedulable agent's architecture should be considered
        assert result == "x86_64"

    @pytest.mark.asyncio
    async def test_excludes_agents_from_other_scaling_groups(
        self,
        deployment_repository: DeploymentRepository,
        test_scaling_group_name: str,
        agents_in_different_scaling_groups: list[AgentId],
    ) -> None:
        """Test that agents from other scaling groups are excluded."""
        result = await deployment_repository.get_default_architecture_from_scaling_group(
            test_scaling_group_name
        )

        # Only target scaling group's agent architecture should be considered
        assert result == "x86_64"

    @pytest.mark.asyncio
    async def test_returns_none_for_nonexistent_scaling_group(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Test that None is returned for non-existent scaling group."""
        result = await deployment_repository.get_default_architecture_from_scaling_group(
            "nonexistent-scaling-group"
        )

        assert result is None
