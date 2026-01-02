"""Tests for DeploymentRepository."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    BinarySize,
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
    ServicePort,
    ServicePortProtocols,
    SessionId,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.errors.deployment import DeploymentRevisionNotFound
from ai.backend.manager.errors.service import AutoScalingPolicyNotFound, DeploymentPolicyNotFound
from ai.backend.manager.models import KeyPairResourcePolicyRow, KeyPairRow
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyData,
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import (
    BlueGreenSpec,
    DeploymentPolicyData,
    DeploymentPolicyRow,
    RollingUpdateSpec,
)
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
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
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators import (
    DeploymentAutoScalingPolicyCreatorSpec,
    DeploymentPolicyCreatorSpec,
    DeploymentRevisionCreatorSpec,
)
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentAutoScalingPolicyUpdaterSpec,
    DeploymentMetadataUpdaterSpec,
    DeploymentPolicyUpdaterSpec,
    DeploymentUpdaterSpec,
    ReplicaSpecUpdaterSpec,
    RevisionStateUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables


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
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                AgentRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                SessionRow,
                KernelRow,
                EndpointRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return sgroup_name

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AgentId:
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
            await db_sess.commit()

        return agent_id

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return group_id

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AccessKey:
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
            await db_sess.commit()

        return access_key

    @pytest.fixture
    async def test_session_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
        test_domain_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> SessionId:
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
            await db_sess.commit()

        return session_id

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
    ) -> tuple[uuid.UUID, str, int]:
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
            await db_sess.commit()

        return (kernel_id, kernel_host, inference_port)

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
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return kernel_id

    @pytest.fixture
    async def test_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return endpoint_id

    @pytest.fixture
    async def test_route_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_session_id: SessionId,
        test_domain_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return route_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance with database and mocked dependencies."""
        # Create mock dependencies
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

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
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                ScalingGroupRow,
                AgentRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return sgroup_name

    @pytest.fixture
    async def other_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return sgroup_name

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

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
    ) -> list[AgentId]:
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

        return agent_ids

    @pytest.fixture
    async def single_aarch64_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AgentId:
        """Create a single aarch64 agent."""
        agent_id = await self._create_agent(
            db_with_cleanup,
            test_scaling_group_name,
            "aarch64",
            suffix="single",
        )
        return agent_id

    @pytest.fixture
    async def alive_x86_and_lost_aarch64_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> list[AgentId]:
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

        return agent_ids

    @pytest.fixture
    async def schedulable_x86_and_non_schedulable_aarch64_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> list[AgentId]:
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

        return agent_ids

    @pytest.fixture
    async def agents_in_different_scaling_groups(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
        other_scaling_group_name: str,
    ) -> list[AgentId]:
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

        return agent_ids

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


class TestDeploymentRevisionOperations:
    """Test cases for deployment revision repository operations."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                GroupRow,
                VFolderRow,
                ImageRow,
                EndpointRow,
                DeploymentRevisionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return sgroup_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return group_id

    @pytest.fixture
    async def test_image_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> uuid.UUID:
        """Create test image and return image ID."""
        async with db_with_cleanup.begin_session() as db_sess:
            image = ImageRow(
                name="test-image:latest",
                project=str(uuid.uuid4()),
                image="test-image",
                registry="docker.io",
                registry_id=uuid.uuid4(),
                architecture="x86_64",
                is_local=False,
                config_digest="sha256:abc123",
                size_bytes=1000000,
                type=ImageType.COMPUTE,
                labels={},
            )
            db_sess.add(image)
            await db_sess.commit()
            image_id = image.id

        return image_id

    @pytest.fixture
    async def test_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
        test_image_id: uuid.UUID,
    ) -> uuid.UUID:
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
                model=None,
                replicas=1,
                image=test_image_id,
                runtime_variant=RuntimeVariant.CUSTOM,
                url=f"http://test-{uuid.uuid4().hex[:8]}.example.com",
                open_to_public=False,
                lifecycle_stage=EndpointLifecycle.CREATED,
                resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
                model_mount_destination="/models",
                cluster_mode=ClusterMode.SINGLE_NODE.name,
                cluster_size=1,
                environ={},
                resource_opts={},
                extra_mounts=[],
            )
            db_sess.add(endpoint)
            await db_sess.commit()

        return endpoint_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

    @pytest.fixture
    async def test_revision_data(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_image_id: uuid.UUID,
        test_scaling_group_name: str,
    ) -> ModelRevisionData:
        """Create a single test revision."""

        spec = DeploymentRevisionCreatorSpec(
            endpoint_id=test_endpoint_id,
            revision_number=1,
            image_id=test_image_id,
            resource_group=test_scaling_group_name,
            resource_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
            resource_opts={},
            cluster_mode=ClusterMode.SINGLE_NODE.name,
            cluster_size=1,
            model_id=None,
            model_mount_destination="/models",
            model_definition_path=None,
            model_definition=None,
            startup_command=None,
            bootstrap_script=None,
            environ={},
            callback_url=None,
            runtime_variant=RuntimeVariant.CUSTOM,
            extra_mounts=[],
        )
        return await deployment_repository.create_revision(Creator(spec=spec))

    @pytest.fixture
    async def test_multiple_revisions(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_image_id: uuid.UUID,
        test_scaling_group_name: str,
    ) -> list[ModelRevisionData]:
        """Create multiple test revisions (revision 1, 2, 3)."""
        revisions: list[ModelRevisionData] = []
        for rev_num in [1, 2, 3]:
            spec = DeploymentRevisionCreatorSpec(
                endpoint_id=test_endpoint_id,
                revision_number=rev_num,
                image_id=test_image_id,
                resource_group=test_scaling_group_name,
                resource_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                resource_opts={},
                cluster_mode=ClusterMode.SINGLE_NODE.name,
                cluster_size=1,
                model_id=None,
                model_mount_destination="/models",
                model_definition_path=None,
                model_definition=None,
                startup_command=None,
                bootstrap_script=None,
                environ={},
                callback_url=None,
                runtime_variant=RuntimeVariant.CUSTOM,
                extra_mounts=[],
            )
            revision = await deployment_repository.create_revision(Creator(spec=spec))
            revisions.append(revision)
        return revisions

    @pytest.fixture
    async def test_five_revisions(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_image_id: uuid.UUID,
        test_scaling_group_name: str,
    ) -> list[ModelRevisionData]:
        """Create 5 test revisions for pagination tests."""
        revisions: list[ModelRevisionData] = []
        for rev_num in range(1, 6):
            spec = DeploymentRevisionCreatorSpec(
                endpoint_id=test_endpoint_id,
                revision_number=rev_num,
                image_id=test_image_id,
                resource_group=test_scaling_group_name,
                resource_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                resource_opts={},
                cluster_mode=ClusterMode.SINGLE_NODE.name,
                cluster_size=1,
                model_id=None,
                model_mount_destination="/models",
                model_definition_path=None,
                model_definition=None,
                startup_command=None,
                bootstrap_script=None,
                environ={},
                callback_url=None,
                runtime_variant=RuntimeVariant.CUSTOM,
                extra_mounts=[],
            )
            revision = await deployment_repository.create_revision(Creator(spec=spec))
            revisions.append(revision)
        return revisions

    @pytest.mark.asyncio
    async def test_create_revision(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_image_id: uuid.UUID,
        test_scaling_group_name: str,
    ) -> None:
        """Test creating a deployment revision using Creator."""
        spec = DeploymentRevisionCreatorSpec(
            endpoint_id=test_endpoint_id,
            revision_number=1,
            image_id=test_image_id,
            resource_group=test_scaling_group_name,
            resource_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
            resource_opts={},
            cluster_mode=ClusterMode.SINGLE_NODE.name,
            cluster_size=1,
            model_id=None,
            model_mount_destination="/models",
            model_definition_path=None,
            model_definition=None,
            startup_command=None,
            bootstrap_script=None,
            environ={},
            callback_url=None,
            runtime_variant=RuntimeVariant.CUSTOM,
            extra_mounts=[],
        )
        creator = Creator(spec=spec)

        result = await deployment_repository.create_revision(creator)

        assert result.id is not None
        assert result.cluster_config.mode == ClusterMode.SINGLE_NODE
        assert result.cluster_config.size == 1
        assert result.resource_config.resource_group_name == test_scaling_group_name
        assert result.model_runtime_config.runtime_variant == RuntimeVariant.CUSTOM
        assert result.name == "revision-1"

    @pytest.mark.asyncio
    async def test_get_revision(
        self,
        deployment_repository: DeploymentRepository,
        test_revision_data: ModelRevisionData,
    ) -> None:
        """Test getting a deployment revision by ID."""
        result = await deployment_repository.get_revision(test_revision_data.id)

        assert result.id == test_revision_data.id
        assert result.name == "revision-1"
        assert result.cluster_config.mode == ClusterMode.SINGLE_NODE

    @pytest.mark.asyncio
    async def test_get_revision_not_found(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Test that get_revision raises DeploymentRevisionNotFound for nonexistent ID."""
        nonexistent_id = uuid.uuid4()

        with pytest.raises(DeploymentRevisionNotFound):
            await deployment_repository.get_revision(nonexistent_id)

    @pytest.mark.asyncio
    async def test_get_latest_revision_number_no_revisions(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test that get_latest_revision_number returns None when no revisions exist."""
        result = await deployment_repository.get_latest_revision_number(test_endpoint_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_revision_number_with_revisions(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_multiple_revisions: list[ModelRevisionData],
    ) -> None:
        """Test that get_latest_revision_number returns correct value."""
        result = await deployment_repository.get_latest_revision_number(test_endpoint_id)

        assert result == 3

    @pytest.mark.asyncio
    async def test_search_revisions_empty(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test search_revisions returns empty result when no revisions exist."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10),
            conditions=[lambda: DeploymentRevisionRow.endpoint == test_endpoint_id],
        )

        result = await deployment_repository.search_revisions(querier)

        assert result.total_count == 0
        assert result.items == []
        assert result.has_next_page is False
        assert result.has_previous_page is False

    @pytest.mark.asyncio
    async def test_search_revisions_with_results(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_multiple_revisions: list[ModelRevisionData],
    ) -> None:
        """Test search_revisions returns correct results."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10),
            conditions=[lambda: DeploymentRevisionRow.endpoint == test_endpoint_id],
        )

        result = await deployment_repository.search_revisions(querier)

        assert result.total_count == 3
        assert len(result.items) == 3
        assert result.has_next_page is False
        assert result.has_previous_page is False

    @pytest.mark.asyncio
    async def test_search_revisions_with_pagination(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_five_revisions: list[ModelRevisionData],
    ) -> None:
        """Test search_revisions respects pagination."""
        # First page
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[lambda: DeploymentRevisionRow.endpoint == test_endpoint_id],
        )
        result = await deployment_repository.search_revisions(querier)

        assert result.total_count == 5
        assert len(result.items) == 2
        assert result.has_next_page is True
        assert result.has_previous_page is False

        # Second page
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=2),
            conditions=[lambda: DeploymentRevisionRow.endpoint == test_endpoint_id],
        )
        result = await deployment_repository.search_revisions(querier)

        assert result.total_count == 5
        assert len(result.items) == 2
        assert result.has_next_page is True
        assert result.has_previous_page is True

    @pytest.mark.asyncio
    async def test_update_endpoint_deploying_revision(
        self,
        deployment_repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_revision_data: ModelRevisionData,
    ) -> None:
        """Test updating endpoint deploying_revision using Updater."""
        updater = Updater(
            spec=RevisionStateUpdaterSpec(
                deploying_revision=TriState.update(test_revision_data.id),
            ),
            pk_value=test_endpoint_id,
        )
        deployment_info = await deployment_repository.update_endpoint(updater)

        # Verify returned DeploymentInfo
        assert deployment_info.id == test_endpoint_id

        # Verify database state (deploying_revision is not part of DeploymentInfo)
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            query = sa.select(EndpointRow).where(EndpointRow.id == test_endpoint_id)
            result = await db_sess.execute(query)
            endpoint = result.scalar_one()
            assert endpoint.deploying_revision == test_revision_data.id

    @pytest.mark.asyncio
    async def test_update_endpoint_current_revision(
        self,
        deployment_repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_revision_data: ModelRevisionData,
    ) -> None:
        """Test updating endpoint current_revision using Updater."""
        updater = Updater(
            spec=RevisionStateUpdaterSpec(
                current_revision=TriState.update(test_revision_data.id),
            ),
            pk_value=test_endpoint_id,
        )
        deployment_info = await deployment_repository.update_endpoint(updater)

        # Verify returned DeploymentInfo
        assert deployment_info.id == test_endpoint_id
        assert deployment_info.current_revision_id == test_revision_data.id

        # Verify database state
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            query = sa.select(EndpointRow).where(EndpointRow.id == test_endpoint_id)
            result = await db_sess.execute(query)
            endpoint = result.scalar_one()
            assert endpoint.current_revision == test_revision_data.id

    @pytest.mark.asyncio
    async def test_update_endpoint_nullify_deploying_revision(
        self,
        deployment_repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_revision_data: ModelRevisionData,
    ) -> None:
        """Test nullifying endpoint deploying_revision using TriState.nullify()."""
        # First set deploying_revision
        updater = Updater(
            spec=RevisionStateUpdaterSpec(
                deploying_revision=TriState.update(test_revision_data.id),
            ),
            pk_value=test_endpoint_id,
        )
        deployment_info = await deployment_repository.update_endpoint(updater)
        assert deployment_info.id == test_endpoint_id

        # Then nullify it
        updater = Updater(
            spec=RevisionStateUpdaterSpec(
                deploying_revision=TriState.nullify(),
            ),
            pk_value=test_endpoint_id,
        )
        deployment_info = await deployment_repository.update_endpoint(updater)
        assert deployment_info.id == test_endpoint_id

        # Verify database state (deploying_revision is not part of DeploymentInfo)
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            query = sa.select(EndpointRow).where(EndpointRow.id == test_endpoint_id)
            result = await db_sess.execute(query)
            endpoint = result.scalar_one()
            assert endpoint.deploying_revision is None

    @pytest.mark.asyncio
    async def test_update_endpoint_returns_updated_deployment_info(
        self,
        deployment_repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_revision_data: ModelRevisionData,
    ) -> None:
        """Test that update_endpoint returns DeploymentInfo with updated values."""
        new_name = "updated-deployment-name"
        new_desired_replica_count = 5

        updater = Updater(
            spec=DeploymentUpdaterSpec(
                metadata=DeploymentMetadataUpdaterSpec(
                    name=OptionalState.update(new_name),
                ),
                replica_spec=ReplicaSpecUpdaterSpec(
                    desired_replica_count=OptionalState.update(new_desired_replica_count),
                ),
                revision_state=RevisionStateUpdaterSpec(
                    current_revision=TriState.update(test_revision_data.id),
                ),
            ),
            pk_value=test_endpoint_id,
        )
        deployment_info = await deployment_repository.update_endpoint(updater)

        # Verify returned DeploymentInfo contains updated values
        assert deployment_info.id == test_endpoint_id
        assert deployment_info.metadata.name == new_name
        assert deployment_info.replica_spec.desired_replica_count == new_desired_replica_count
        assert deployment_info.current_revision_id == test_revision_data.id

        # Verify database state matches returned values
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            query = sa.select(EndpointRow).where(EndpointRow.id == test_endpoint_id)
            result = await db_sess.execute(query)
            endpoint = result.scalar_one()
            assert endpoint.name == new_name
            assert endpoint.desired_replicas == new_desired_replica_count
            assert endpoint.current_revision == test_revision_data.id


class TestDeploymentAutoScalingPolicyOperations:
    """Test cases for deployment auto-scaling policy repository operations."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                GroupRow,
                VFolderRow,
                EndpointRow,
                DeploymentAutoScalingPolicyRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return sgroup_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return group_id

    @pytest.fixture
    async def test_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> uuid.UUID:
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
                model=None,
                desired_replicas=1,
                image=None,
                runtime_variant=RuntimeVariant.CUSTOM,
                url=f"http://test-{uuid.uuid4().hex[:8]}.example.com",
                open_to_public=False,
                lifecycle_stage=EndpointLifecycle.DESTROYED,
                resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
            )
            db_sess.add(endpoint)
            await db_sess.commit()

        return endpoint_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

    @pytest.fixture
    async def test_auto_scaling_policy_data(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
    ) -> DeploymentAutoScalingPolicyData:
        """Create a single test auto-scaling policy."""
        spec = DeploymentAutoScalingPolicyCreatorSpec(
            endpoint_id=test_endpoint_id,
            min_replicas=1,
            max_replicas=10,
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu_utilization",
            comparator=AutoScalingMetricComparator.GREATER_THAN_OR_EQUAL,
            scale_up_threshold=Decimal("80"),
            scale_down_threshold=Decimal("20"),
            scale_up_step_size=2,
            scale_down_step_size=1,
            cooldown_seconds=300,
        )
        return await deployment_repository.create_auto_scaling_policy(Creator(spec=spec))

    @pytest.mark.asyncio
    async def test_create_auto_scaling_policy(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test creating an auto-scaling policy using Creator."""
        spec = DeploymentAutoScalingPolicyCreatorSpec(
            endpoint_id=test_endpoint_id,
            min_replicas=2,
            max_replicas=20,
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu_utilization",
            comparator=AutoScalingMetricComparator.GREATER_THAN,
            scale_up_threshold=Decimal("70"),
            scale_down_threshold=Decimal("30"),
            scale_up_step_size=3,
            scale_down_step_size=2,
            cooldown_seconds=600,
        )
        creator = Creator(spec=spec)

        result = await deployment_repository.create_auto_scaling_policy(creator)

        assert result.id is not None
        assert result.endpoint == test_endpoint_id
        assert result.min_replicas == 2
        assert result.max_replicas == 20
        assert result.metric_source == AutoScalingMetricSource.KERNEL
        assert result.metric_name == "cpu_utilization"
        assert result.comparator == AutoScalingMetricComparator.GREATER_THAN
        assert result.scale_up_threshold == Decimal("70")
        assert result.scale_down_threshold == Decimal("30")
        assert result.scale_up_step_size == 3
        assert result.scale_down_step_size == 2
        assert result.cooldown_seconds == 600

    @pytest.mark.asyncio
    async def test_get_auto_scaling_policy(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_auto_scaling_policy_data: DeploymentAutoScalingPolicyData,
    ) -> None:
        """Test getting an auto-scaling policy by endpoint ID."""
        result = await deployment_repository.get_auto_scaling_policy(test_endpoint_id)

        assert result.id == test_auto_scaling_policy_data.id
        assert result.endpoint == test_endpoint_id
        assert result.min_replicas == 1
        assert result.max_replicas == 10
        assert result.metric_source == AutoScalingMetricSource.KERNEL
        assert result.metric_name == "cpu_utilization"

    @pytest.mark.asyncio
    async def test_get_auto_scaling_policy_not_found(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test that get_auto_scaling_policy raises AutoScalingPolicyNotFound."""
        with pytest.raises(AutoScalingPolicyNotFound):
            await deployment_repository.get_auto_scaling_policy(test_endpoint_id)

    @pytest.mark.asyncio
    async def test_update_auto_scaling_policy(
        self,
        deployment_repository: DeploymentRepository,
        test_auto_scaling_policy_data: DeploymentAutoScalingPolicyData,
    ) -> None:
        """Test updating an auto-scaling policy using Updater."""
        updater = Updater(
            spec=DeploymentAutoScalingPolicyUpdaterSpec(
                min_replicas=OptionalState.update(5),
                max_replicas=OptionalState.update(50),
                scale_up_threshold=TriState.update(Decimal("90")),
            ),
            pk_value=test_auto_scaling_policy_data.id,
        )

        result = await deployment_repository.update_auto_scaling_policy(updater)

        assert result.id == test_auto_scaling_policy_data.id
        assert result.min_replicas == 5
        assert result.max_replicas == 50
        assert result.scale_up_threshold == Decimal("90")
        # Unchanged fields should remain the same
        assert result.scale_down_threshold == Decimal("20")
        assert result.cooldown_seconds == 300

    @pytest.mark.asyncio
    async def test_update_auto_scaling_policy_not_found(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Test that update_auto_scaling_policy raises AutoScalingPolicyNotFound."""
        nonexistent_id = uuid.uuid4()
        updater = Updater(
            spec=DeploymentAutoScalingPolicyUpdaterSpec(
                min_replicas=OptionalState.update(5),
            ),
            pk_value=nonexistent_id,
        )

        with pytest.raises(AutoScalingPolicyNotFound):
            await deployment_repository.update_auto_scaling_policy(updater)

    @pytest.mark.asyncio
    async def test_delete_auto_scaling_policy(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_auto_scaling_policy_data: DeploymentAutoScalingPolicyData,
    ) -> None:
        """Test deleting an auto-scaling policy using Purger."""
        purger = Purger(
            row_class=DeploymentAutoScalingPolicyRow,
            pk_value=test_auto_scaling_policy_data.id,
        )

        result = await deployment_repository.delete_auto_scaling_policy(purger)

        assert result is not None
        assert result.row.id == test_auto_scaling_policy_data.id

        # Verify the policy no longer exists
        with pytest.raises(AutoScalingPolicyNotFound):
            await deployment_repository.get_auto_scaling_policy(test_endpoint_id)

    @pytest.mark.asyncio
    async def test_delete_auto_scaling_policy_not_found(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Test that delete_auto_scaling_policy returns None for nonexistent policy."""
        nonexistent_id = uuid.uuid4()
        purger = Purger(
            row_class=DeploymentAutoScalingPolicyRow,
            pk_value=nonexistent_id,
        )

        result = await deployment_repository.delete_auto_scaling_policy(purger)

        assert result is None


class TestDeploymentPolicyOperations:
    """Test cases for deployment policy repository operations."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                GroupRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return sgroup_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return group_id

    @pytest.fixture
    async def test_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> uuid.UUID:
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
                model=None,
                desired_replicas=1,
                image=None,
                runtime_variant=RuntimeVariant.CUSTOM,
                url=f"http://test-{uuid.uuid4().hex[:8]}.example.com",
                open_to_public=False,
                lifecycle_stage=EndpointLifecycle.DESTROYED,
                resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
            )
            db_sess.add(endpoint)
            await db_sess.commit()

        return endpoint_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

    @pytest.fixture
    async def test_deployment_policy_data(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
    ) -> DeploymentPolicyData:
        """Create a single test deployment policy."""
        spec = DeploymentPolicyCreatorSpec(
            endpoint_id=test_endpoint_id,
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(max_surge=1, max_unavailable=0),
            rollback_on_failure=False,
        )
        return await deployment_repository.create_deployment_policy(Creator(spec=spec))

    @pytest.mark.asyncio
    async def test_create_deployment_policy(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test creating a deployment policy using Creator."""
        spec = DeploymentPolicyCreatorSpec(
            endpoint_id=test_endpoint_id,
            strategy=DeploymentStrategy.BLUE_GREEN,
            strategy_spec=BlueGreenSpec(auto_promote=True, promote_delay_seconds=60),
            rollback_on_failure=False,
        )
        creator = Creator(spec=spec)

        result = await deployment_repository.create_deployment_policy(creator)

        assert result.id is not None
        assert result.endpoint == test_endpoint_id
        assert result.strategy == DeploymentStrategy.BLUE_GREEN
        assert result.strategy_spec == BlueGreenSpec(auto_promote=True, promote_delay_seconds=60)
        assert result.rollback_on_failure is False

    @pytest.mark.asyncio
    async def test_get_deployment_policy(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_deployment_policy_data: DeploymentPolicyData,
    ) -> None:
        """Test getting a deployment policy by endpoint ID."""
        result = await deployment_repository.get_deployment_policy(test_endpoint_id)

        assert result.id == test_deployment_policy_data.id
        assert result.endpoint == test_endpoint_id
        assert result.strategy == DeploymentStrategy.ROLLING
        assert result.strategy_spec == RollingUpdateSpec(max_surge=1, max_unavailable=0)

    @pytest.mark.asyncio
    async def test_get_deployment_policy_not_found(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test that get_deployment_policy raises DeploymentPolicyNotFound."""
        with pytest.raises(DeploymentPolicyNotFound):
            await deployment_repository.get_deployment_policy(test_endpoint_id)

    @pytest.mark.asyncio
    async def test_update_deployment_policy(
        self,
        deployment_repository: DeploymentRepository,
        test_deployment_policy_data: DeploymentPolicyData,
    ) -> None:
        """Test updating a deployment policy using Updater."""
        new_strategy_spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=30)
        updater = Updater(
            spec=DeploymentPolicyUpdaterSpec(
                strategy=OptionalState.update(DeploymentStrategy.BLUE_GREEN),
                strategy_spec=OptionalState.update(new_strategy_spec),
                rollback_on_failure=OptionalState.update(True),
            ),
            pk_value=test_deployment_policy_data.id,
        )

        result = await deployment_repository.update_deployment_policy(updater)

        assert result.id == test_deployment_policy_data.id
        assert result.strategy == DeploymentStrategy.BLUE_GREEN
        assert result.strategy_spec == new_strategy_spec
        assert result.rollback_on_failure is True

    @pytest.mark.asyncio
    async def test_update_deployment_policy_not_found(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Test that update_deployment_policy raises DeploymentPolicyNotFound."""
        nonexistent_id = uuid.uuid4()
        updater = Updater(
            spec=DeploymentPolicyUpdaterSpec(
                strategy=OptionalState.update(DeploymentStrategy.BLUE_GREEN),
            ),
            pk_value=nonexistent_id,
        )

        with pytest.raises(DeploymentPolicyNotFound):
            await deployment_repository.update_deployment_policy(updater)

    @pytest.mark.asyncio
    async def test_delete_deployment_policy(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_deployment_policy_data: DeploymentPolicyData,
    ) -> None:
        """Test deleting a deployment policy using Purger."""
        purger = Purger(
            row_class=DeploymentPolicyRow,
            pk_value=test_deployment_policy_data.id,
        )

        result = await deployment_repository.delete_deployment_policy(purger)

        assert result is not None
        assert result.row.id == test_deployment_policy_data.id

        # Verify the policy no longer exists
        with pytest.raises(DeploymentPolicyNotFound):
            await deployment_repository.get_deployment_policy(test_endpoint_id)

    @pytest.mark.asyncio
    async def test_delete_deployment_policy_not_found(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Test that delete_deployment_policy returns None for nonexistent policy."""
        nonexistent_id = uuid.uuid4()
        purger = Purger(
            row_class=DeploymentPolicyRow,
            pk_value=nonexistent_id,
        )

        result = await deployment_repository.delete_deployment_policy(purger)

        assert result is None


class TestRouteOperations:
    """Test cases for route repository operations."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                GroupRow,
                VFolderRow,
                EndpointRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return sgroup_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
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
            await db_sess.commit()

        return group_id

    @pytest.fixture
    async def test_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_user_uuid: uuid.UUID,
        test_group_id: uuid.UUID,
    ) -> uuid.UUID:
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
                model=None,
                desired_replicas=1,
                image=None,
                runtime_variant=RuntimeVariant.CUSTOM,
                url=f"http://test-{uuid.uuid4().hex[:8]}.example.com",
                open_to_public=False,
                lifecycle_stage=EndpointLifecycle.DESTROYED,  # DESTROYED allows null image
                resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
            )
            db_sess.add(endpoint)
            await db_sess.commit()

        return endpoint_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

    @pytest.mark.asyncio
    async def test_create_route(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_domain_name: str,
        test_group_id: uuid.UUID,
    ) -> None:
        """Test creating a route using Creator with RouteCreatorSpec."""
        from ai.backend.manager.data.deployment.types import RouteTrafficStatus
        from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec

        spec = RouteCreatorSpec(
            endpoint_id=test_endpoint_id,
            session_owner_id=test_user_uuid,
            domain=test_domain_name,
            project_id=test_group_id,
            traffic_ratio=1.0,
            revision_id=None,
            traffic_status=RouteTrafficStatus.ACTIVE,
        )
        creator = Creator(spec=spec)

        route_id = await deployment_repository.create_route(creator)

        assert route_id is not None
        assert isinstance(route_id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_update_route_status(
        self,
        deployment_repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_domain_name: str,
        test_group_id: uuid.UUID,
    ) -> None:
        """Test updating route status using RouteStatusUpdaterSpec."""
        from ai.backend.manager.data.deployment.types import (
            RouteStatus,
            RouteTrafficStatus,
        )
        from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
        from ai.backend.manager.repositories.deployment.updaters import RouteStatusUpdaterSpec
        from ai.backend.manager.types import OptionalState

        # Create a route first
        spec = RouteCreatorSpec(
            endpoint_id=test_endpoint_id,
            session_owner_id=test_user_uuid,
            domain=test_domain_name,
            project_id=test_group_id,
        )
        route_id = await deployment_repository.create_route(Creator(spec=spec))

        # Update the route status
        updater = Updater(
            spec=RouteStatusUpdaterSpec(
                status=OptionalState.update(RouteStatus.HEALTHY),
                traffic_status=OptionalState.update(RouteTrafficStatus.INACTIVE),
            ),
            pk_value=route_id,
        )
        result = await deployment_repository.update_route(updater)

        assert result is True

        # Verify the update
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            query = sa.select(RoutingRow).where(RoutingRow.id == route_id)
            db_result = await db_sess.execute(query)
            route = db_result.scalar_one()
            assert route.status == RouteStatus.HEALTHY
            assert route.traffic_status == RouteTrafficStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_update_route_with_unified_spec(
        self,
        deployment_repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_domain_name: str,
        test_group_id: uuid.UUID,
    ) -> None:
        """Test updating route using unified RouteUpdaterSpec."""
        from ai.backend.manager.data.deployment.types import (
            RouteStatus,
            RouteTrafficStatus,
        )
        from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
        from ai.backend.manager.repositories.deployment.updaters import RouteUpdaterSpec
        from ai.backend.manager.types import OptionalState

        # Create a route first
        spec = RouteCreatorSpec(
            endpoint_id=test_endpoint_id,
            session_owner_id=test_user_uuid,
            domain=test_domain_name,
            project_id=test_group_id,
        )
        route_id = await deployment_repository.create_route(Creator(spec=spec))

        # Update the route using unified spec (excluding session to avoid FK constraint)
        updater = Updater(
            spec=RouteUpdaterSpec(
                status=OptionalState.update(RouteStatus.HEALTHY),
                traffic_status=OptionalState.update(RouteTrafficStatus.ACTIVE),
                traffic_ratio=OptionalState.update(0.5),
            ),
            pk_value=route_id,
        )
        result = await deployment_repository.update_route(updater)

        assert result is True

        # Verify the update
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            query = sa.select(RoutingRow).where(RoutingRow.id == route_id)
            db_result = await db_sess.execute(query)
            route = db_result.scalar_one()
            assert route.status == RouteStatus.HEALTHY
            assert route.traffic_status == RouteTrafficStatus.ACTIVE
            assert route.traffic_ratio == 0.5

    @pytest.mark.asyncio
    async def test_update_route_not_found(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Test that update_route returns False for nonexistent route."""
        from ai.backend.manager.data.deployment.types import RouteStatus
        from ai.backend.manager.repositories.deployment.updaters import RouteStatusUpdaterSpec
        from ai.backend.manager.types import OptionalState

        nonexistent_id = uuid.uuid4()
        updater = Updater(
            spec=RouteStatusUpdaterSpec(
                status=OptionalState.update(RouteStatus.HEALTHY),
            ),
            pk_value=nonexistent_id,
        )

        result = await deployment_repository.update_route(updater)

        assert result is False
