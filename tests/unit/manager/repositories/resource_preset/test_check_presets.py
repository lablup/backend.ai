"""
Integration tests for check_presets method.

Tests verify that occupied slots are calculated from actual kernel states
(RUNNING, TERMINATING) instead of cached AgentRow.occupied_slots.

Addresses BA-3054: Wrong parse of inference metrics.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
    SlotName,
    SlotTypes,
    ValkeyTarget,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserRole
from ai.backend.manager.models import (
    AgentRow,
    DomainRow,
    GroupRow,
    KernelRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    ProjectResourcePolicyRow,
    ScalingGroupOpts,
    ScalingGroupRow,
    SessionRow,
    UserResourcePolicyRow,
    UserRow,
    association_groups_users,
    sgroups_for_domains,
    sgroups_for_groups,
    sgroups_for_keypairs,
)
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_preset.repository import (
    ResourcePresetRepository,
)
from ai.backend.manager.repositories.resource_preset.types import (
    CheckPresetsResult,
)
from ai.backend.testutils.db import with_tables


class TestCheckPresetsOccupiedSlots:
    """
    Integration tests for check_presets verifying occupied slot calculation
    from actual kernel statuses (RUNNING, TERMINATING) instead of cached values.
    """

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ProjectResourcePolicyRow,
                ScalingGroupRow,
                ResourcePresetRow,
                sgroups_for_domains,  # association table
                UserRow,
                KeyPairRow,
                sgroups_for_keypairs,  # association table
                GroupRow,
                sgroups_for_groups,  # association table
                association_groups_users,  # association table
                AgentRow,
                SessionRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name"""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("1000"),
                    "mem": Decimal("1048576"),
                }),
            )
            db_sess.add(domain)
            await db_sess.flush()

        try:
            yield domain_name
        finally:
            # Cleanup handled by db_with_cleanup
            pass

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return scaling group name"""
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                driver="test-driver",
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
                    pending_timeout=timedelta(seconds=300),
                    agent_selection_strategy=AgentSelectionStrategy.ROUNDROBIN,
                ),
                driver_opts={},
                use_host_network=False,
                is_active=True,
            )
            db_sess.add(sg)
            await db_sess.flush()

            # Associate scaling group with domain
            await db_sess.execute(
                sa.insert(sgroups_for_domains).values(
                    scaling_group=sg_name,
                    domain=test_domain_name,
                )
            )
            await db_sess.flush()

        try:
            yield sg_name
        finally:
            # Cleanup handled by db_with_cleanup
            pass

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policies and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            user_policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            kp_policy = KeyPairResourcePolicyRow(
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
            db_sess.add(user_policy)
            db_sess.add(project_policy)
            db_sess.add(kp_policy)
            await db_sess.flush()

        try:
            yield policy_name
        finally:
            # Cleanup handled by db_with_cleanup
            pass

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
        test_user_uuid: uuid.UUID,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test group and return group ID"""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{group_id.hex[:8]}",
                domain_name=test_domain_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("500"),
                    "mem": Decimal("524288"),
                }),
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(group)
            await db_sess.flush()

            # Add user to group
            await db_sess.execute(
                sa.insert(association_groups_users).values(
                    user_id=test_user_uuid,
                    group_id=group_id,
                )
            )
            await db_sess.flush()

        try:
            yield group_id
        finally:
            # Cleanup handled by db_with_cleanup
            pass

    @pytest.fixture
    async def test_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group_id: uuid.UUID,
    ) -> AsyncGenerator[str, None]:
        """Get group name from group ID"""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            group_result = await db_sess.execute(
                sa.select(GroupRow.name).where(GroupRow.id == test_group_id)
            )
            group_name = group_result.scalar_one()

        try:
            yield group_name
        finally:
            pass

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test user and return user UUID"""
        user_uuid = uuid.uuid4()

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        try:
            yield user_uuid
        finally:
            # Cleanup handled by db_with_cleanup
            pass

    @pytest.fixture
    async def test_keypair_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        """Create test keypair and return access key"""
        access_key = AccessKey(f"test-ak-{uuid.uuid4().hex[:8]}")

        async with db_with_cleanup.begin_session() as db_sess:
            # Get user email for user_id field
            user_result = await db_sess.execute(
                sa.select(UserRow.email).where(UserRow.uuid == test_user_uuid)
            )
            user_email = user_result.scalar_one()

            keypair = KeyPairRow(
                access_key=access_key,
                secret_key="test-secret",
                user_id=user_email,  # user_id is email (string)
                user=test_user_uuid,  # user is UUID (required NOT NULL)
                is_active=True,
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(keypair)
            await db_sess.flush()

        try:
            yield access_key
        finally:
            # Cleanup handled by db_with_cleanup
            pass

    async def _create_agent(
        self,
        db: ExtendedAsyncSAEngine,
        scaling_group_name: str,
        addr: str,
        *,
        status: AgentStatus = AgentStatus.ALIVE,
        available_slots: Optional[ResourceSlot] = None,
        occupied_slots: Optional[ResourceSlot] = None,
        schedulable: bool = True,
    ) -> AgentId:
        """Helper method to create an agent with specified status and resources."""
        agent_id = AgentId(f"agent-{status.name.lower()}-{uuid.uuid4().hex[:8]}")
        async with db.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=status,
                status_changed=datetime.now(tzutc()),
                region="test-region",
                scaling_group=scaling_group_name,
                schedulable=schedulable,
                available_slots=available_slots
                or ResourceSlot({"cpu": Decimal("16"), "mem": Decimal("32768")}),
                occupied_slots=occupied_slots
                or ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
                addr=addr,
                version="v25.03.0",
                architecture="x86_64",
            )
            db_sess.add(agent)
            await db_sess.flush()
        return agent_id

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AgentId:
        """Create test ALIVE agent and return agent ID"""
        return await self._create_agent(
            db_with_cleanup,
            test_scaling_group_name,
            "10.0.0.1:2001",
        )

    @pytest.fixture
    async def alive_and_non_alive_agents(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> list[AgentId]:
        """Given: ALIVE and non-ALIVE agents exist in the scaling group."""
        non_alive_slots = ResourceSlot({"cpu": Decimal("100"), "mem": Decimal("204800")})

        agent_ids: list[AgentId] = []

        # Create ALIVE agents (should be counted): 2 x 16 CPU, 32GB
        agent_ids.append(
            await self._create_agent(db_with_cleanup, test_scaling_group_name, "10.0.0.1:2001")
        )
        agent_ids.append(
            await self._create_agent(db_with_cleanup, test_scaling_group_name, "10.0.0.2:2001")
        )

        # Create non-ALIVE agents (should be excluded): 3 x 100 CPU, 200GB
        agent_ids.append(
            await self._create_agent(
                db_with_cleanup,
                test_scaling_group_name,
                "10.0.0.3:2001",
                status=AgentStatus.LOST,
                available_slots=non_alive_slots,
            )
        )
        agent_ids.append(
            await self._create_agent(
                db_with_cleanup,
                test_scaling_group_name,
                "10.0.0.4:2001",
                status=AgentStatus.TERMINATED,
                available_slots=non_alive_slots,
            )
        )
        agent_ids.append(
            await self._create_agent(
                db_with_cleanup,
                test_scaling_group_name,
                "10.0.0.5:2001",
                status=AgentStatus.RESTARTING,
                available_slots=non_alive_slots,
            )
        )

        return agent_ids

    @pytest.fixture
    async def test_resource_policy_dict(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_resource_policy_name: str,
    ) -> dict[str, str]:
        """Get resource policy dict for check_presets API"""
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kp_policy_result = await db_sess.execute(
                sa.select(KeyPairResourcePolicyRow).where(
                    KeyPairResourcePolicyRow.name == test_resource_policy_name
                )
            )
            kp_policy = kp_policy_result.scalar_one()
            return {
                "total_resource_slots": kp_policy.total_resource_slots.to_json(),
                "default_for_unspecified": str(kp_policy.default_for_unspecified),
            }

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Create mocked ManagerConfigProvider for repository"""
        mock = MagicMock()
        # Mock legacy etcd config loader
        mock.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value={
                SlotName("cpu"): SlotTypes("count"),
                SlotName("mem"): SlotTypes("bytes"),
                SlotName("cuda.device"): SlotTypes("count"),
            }
        )
        mock.legacy_etcd_config_loader.get_raw = AsyncMock(
            return_value="true"  # group_resource_visibility
        )
        return mock

    @pytest.fixture
    async def valkey_stat_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyStatClient, None]:
        """Create ValkeyStatClient with real Redis container"""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyStatClient.create(
            valkey_target=valkey_target,
            db_id=0,
            human_readable_name="test-valkey-stat-preset",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    async def repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        valkey_stat_client: ValkeyStatClient,
        mock_config_provider: MagicMock,
    ) -> AsyncGenerator[ResourcePresetRepository, None]:
        """Create ResourcePresetRepository instance with real cache"""
        repo = ResourcePresetRepository(
            db=db_with_cleanup,
            valkey_stat=valkey_stat_client,
            config_provider=mock_config_provider,
        )
        yield repo

    async def test_running_kernels_count_towards_occupied_slots(
        self,
        repository: ResourcePresetRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_resource_policy_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair_access_key: AccessKey,
        test_agent_id: AgentId,
    ) -> None:
        """
        Test that RUNNING kernels contribute to occupied slots.
        Expected: available_slots - RUNNING kernel's occupied_slots
        Tests both DB source and cache layer (cache miss → DB fetch).
        """
        async with db_with_cleanup.begin_session() as db_sess:
            # Create session and kernel with RUNNING status
            session_id = SessionId(uuid.uuid4())
            session = SessionRow(
                id=session_id,
                name=f"test-session-{session_id.hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                status=SessionStatus.RUNNING,
                status_data={},
                created_at=datetime.now(tzutc()),
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_keypair_access_key,
                scaling_group_name=test_scaling_group_name,
                result=SessionResult.UNDEFINED,
                agent_ids=[],
                designated_agent_ids=[],
                target_sgroup_names=[],
                images=[],
                vfolder_mounts=[],
            )

            kernel = KernelRow(
                id=uuid.uuid4(),
                session_id=session.id,
                agent=test_agent_id,
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_keypair_access_key,
                image="test-image:latest",
                status=KernelStatus.RUNNING,
                status_changed=datetime.now(tzutc()),
                status_data={},
                cluster_role="main",
                cluster_idx=1,
                cluster_hostname="main",
                occupied_slots=ResourceSlot({
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                }),
                requested_slots=ResourceSlot({
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                }),
                vfolder_mounts=[],
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
            )

            db_sess.add(session)
            db_sess.add(kernel)
            await db_sess.flush()

        # Test: Repository.check_presets should calculate from kernel (cache miss → DB)
        # Get group name for the API call
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            group_result = await db_sess.execute(
                sa.select(GroupRow.name).where(GroupRow.id == test_group_id)
            )
            group_name = group_result.scalar_one()

        # Get resource policy data
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kp_policy_result = await db_sess.execute(
                sa.select(KeyPairResourcePolicyRow).where(
                    KeyPairResourcePolicyRow.name == test_resource_policy_name
                )
            )
            kp_policy = kp_policy_result.scalar_one()
            resource_policy_dict = {
                "total_resource_slots": kp_policy.total_resource_slots.to_json(),
                "default_for_unspecified": str(kp_policy.default_for_unspecified),
            }

        result: CheckPresetsResult = await repository.check_presets(
            access_key=test_keypair_access_key,
            user_id=test_user_uuid,
            group_name=group_name,
            domain_name=test_domain_name,
            resource_policy=resource_policy_dict,
            scaling_group=test_scaling_group_name,
        )

        # Verify: available (16 CPU, 32GB) - occupied (4 CPU, 8GB) = remaining (12 CPU, 24GB)
        sg_data = result.scaling_groups[test_scaling_group_name]
        assert sg_data.remaining["cpu"] == Decimal("12")
        assert sg_data.remaining["mem"] == Decimal("24576")
        assert sg_data.using["cpu"] == Decimal("4")
        assert sg_data.using["mem"] == Decimal("8192")

    async def test_terminating_kernels_count_towards_occupied_slots(
        self,
        repository: ResourcePresetRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_resource_policy_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair_access_key: AccessKey,
        test_agent_id: AgentId,
    ) -> None:
        """
        Test that TERMINATING kernels also contribute to occupied slots.
        Tests Repository layer with cache miss → DB fetch.
        """
        async with db_with_cleanup.begin_session() as db_sess:
            # Create session and kernel with TERMINATING status
            session_id = SessionId(uuid.uuid4())
            session = SessionRow(
                id=session_id,
                name=f"test-session-{session_id.hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                status=SessionStatus.TERMINATING,
                status_data={},
                created_at=datetime.now(tzutc()),
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_keypair_access_key,
                scaling_group_name=test_scaling_group_name,
                result=SessionResult.UNDEFINED,
                agent_ids=[],
                designated_agent_ids=[],
                target_sgroup_names=[],
                images=["test-image:latest"],
                vfolder_mounts=[],
            )

            kernel = KernelRow(
                id=uuid.uuid4(),
                session_id=session.id,
                agent=test_agent_id,
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_keypair_access_key,
                image="test-image:latest",
                status=KernelStatus.TERMINATING,
                status_changed=datetime.now(tzutc()),
                status_data={},
                cluster_role="main",
                cluster_idx=1,
                cluster_hostname="main",
                occupied_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                }),
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                }),
                vfolder_mounts=[],
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
            )

            db_sess.add(session)
            db_sess.add(kernel)
            await db_sess.flush()

        # Test: Repository.check_presets should include TERMINATING kernels
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            group_result = await db_sess.execute(
                sa.select(GroupRow.name).where(GroupRow.id == test_group_id)
            )
            group_name = group_result.scalar_one()

        # Get resource policy data
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kp_policy_result = await db_sess.execute(
                sa.select(KeyPairResourcePolicyRow).where(
                    KeyPairResourcePolicyRow.name == test_resource_policy_name
                )
            )
            kp_policy = kp_policy_result.scalar_one()
            resource_policy_dict = {
                "total_resource_slots": kp_policy.total_resource_slots.to_json(),
                "default_for_unspecified": str(kp_policy.default_for_unspecified),
            }

        result: CheckPresetsResult = await repository.check_presets(
            access_key=test_keypair_access_key,
            user_id=test_user_uuid,
            group_name=group_name,
            domain_name=test_domain_name,
            resource_policy=resource_policy_dict,
            scaling_group=test_scaling_group_name,
        )

        # Verify: available (16 CPU, 32GB) - occupied (2 CPU, 4GB) = remaining (14 CPU, 28GB)
        sg_data = result.scaling_groups[test_scaling_group_name]
        assert sg_data.remaining["cpu"] == Decimal("14")
        assert sg_data.remaining["mem"] == Decimal("28672")
        assert sg_data.using["cpu"] == Decimal("2")
        assert sg_data.using["mem"] == Decimal("4096")

    async def test_pending_kernels_do_not_count_towards_occupied_slots(
        self,
        repository: ResourcePresetRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_resource_policy_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair_access_key: AccessKey,
        test_agent_id: AgentId,
    ) -> None:
        """
        Test that PENDING kernels DO NOT contribute to occupied slots.
        Tests Repository layer with cache miss → DB fetch.
        """
        async with db_with_cleanup.begin_session() as db_sess:
            # Create session and kernel with PENDING status
            session_id = SessionId(uuid.uuid4())
            session = SessionRow(
                id=session_id,
                name=f"test-session-{session_id.hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                status=SessionStatus.PENDING,
                status_data={},
                created_at=datetime.now(tzutc()),
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_keypair_access_key,
                scaling_group_name=test_scaling_group_name,
                result=SessionResult.UNDEFINED,
                agent_ids=[],
                designated_agent_ids=[],
                target_sgroup_names=[],
                images=["test-image:latest"],
                vfolder_mounts=[],
            )

            kernel = KernelRow(
                id=uuid.uuid4(),
                session_id=session.id,
                agent=test_agent_id,
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_keypair_access_key,
                image="test-image:latest",
                status=KernelStatus.PENDING,
                status_changed=datetime.now(tzutc()),
                status_data={},
                cluster_role="main",
                cluster_idx=1,
                cluster_hostname="main",
                occupied_slots=ResourceSlot({  # Not yet occupied
                    "cpu": Decimal("0"),
                    "mem": Decimal("0"),
                }),
                requested_slots=ResourceSlot({
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                }),
                vfolder_mounts=[],
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
            )

            db_sess.add(session)
            db_sess.add(kernel)
            await db_sess.flush()

        # Test: Repository.check_presets should ignore PENDING kernels
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            group_result = await db_sess.execute(
                sa.select(GroupRow.name).where(GroupRow.id == test_group_id)
            )
            group_name = group_result.scalar_one()

        # Get resource policy data
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kp_policy_result = await db_sess.execute(
                sa.select(KeyPairResourcePolicyRow).where(
                    KeyPairResourcePolicyRow.name == test_resource_policy_name
                )
            )
            kp_policy = kp_policy_result.scalar_one()
            resource_policy_dict = {
                "total_resource_slots": kp_policy.total_resource_slots.to_json(),
                "default_for_unspecified": str(kp_policy.default_for_unspecified),
            }

        result: CheckPresetsResult = await repository.check_presets(
            access_key=test_keypair_access_key,
            user_id=test_user_uuid,
            group_name=group_name,
            domain_name=test_domain_name,
            resource_policy=resource_policy_dict,
            scaling_group=test_scaling_group_name,
        )

        # Verify: available (16 CPU, 32GB) - occupied (0) = remaining (16 CPU, 32GB)
        sg_data = result.scaling_groups[test_scaling_group_name]
        assert sg_data.remaining["cpu"] == Decimal("16")
        assert sg_data.remaining["mem"] == Decimal("32768")
        assert sg_data.using["cpu"] == Decimal("0")
        assert sg_data.using["mem"] == Decimal("0")

    async def test_ignores_cached_occupied_slots_in_agent_row(
        self,
        repository: ResourcePresetRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_resource_policy_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair_access_key: AccessKey,
    ) -> None:
        """
        Test that Repository.check_presets ignores AgentRow.occupied_slots (cached value)
        and calculates from actual kernel states even when cached value is wrong.
        Tests Repository layer with cache miss → DB fetch.
        """
        # Create agent with WRONG cached occupied_slots
        agent_id = AgentId(f"agent-wrong-cache-{uuid.uuid4().hex[:8]}")

        async with db_with_cleanup.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(tzutc()),
                region="test-region",
                scaling_group=test_scaling_group_name,
                schedulable=True,
                available_slots=ResourceSlot({
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                }),
                occupied_slots=ResourceSlot({
                    # WRONG: cached value says 10 CPU occupied
                    "cpu": Decimal("10"),
                    "mem": Decimal("20480"),
                }),
                addr="10.0.0.2:2001",
                version="v25.03.0",
                architecture="x86_64",
            )
            db_sess.add(agent)
            await db_sess.flush()

            # Create session and RUNNING kernel with ACTUAL occupied slots
            session_id = SessionId(uuid.uuid4())
            session = SessionRow(
                id=session_id,
                name=f"test-session-{session_id.hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                status=SessionStatus.RUNNING,
                status_data={},
                created_at=datetime.now(tzutc()),
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_keypair_access_key,
                scaling_group_name=test_scaling_group_name,
                result=SessionResult.UNDEFINED,
                agent_ids=[],
                designated_agent_ids=[],
                target_sgroup_names=[],
                images=[],
                vfolder_mounts=[],
            )

            kernel = KernelRow(
                id=uuid.uuid4(),
                session_id=session.id,
                agent=agent_id,
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_keypair_access_key,
                image="test-image:latest",
                status=KernelStatus.RUNNING,
                status_changed=datetime.now(tzutc()),
                status_data={},
                cluster_role="main",
                cluster_idx=1,
                cluster_hostname="main",
                occupied_slots=ResourceSlot({
                    # ACTUAL: only 3 CPU occupied
                    "cpu": Decimal("3"),
                    "mem": Decimal("6144"),
                }),
                requested_slots=ResourceSlot({
                    "cpu": Decimal("3"),
                    "mem": Decimal("6144"),
                }),
                vfolder_mounts=[],
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
            )

            db_sess.add(session)
            db_sess.add(kernel)
            await db_sess.flush()

        # Test: Repository.check_presets should use ACTUAL kernel occupied slots, not cached agent value
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            group_result = await db_sess.execute(
                sa.select(GroupRow.name).where(GroupRow.id == test_group_id)
            )
            group_name = group_result.scalar_one()

        # Get resource policy data
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kp_policy_result = await db_sess.execute(
                sa.select(KeyPairResourcePolicyRow).where(
                    KeyPairResourcePolicyRow.name == test_resource_policy_name
                )
            )
            kp_policy = kp_policy_result.scalar_one()
            resource_policy_dict = {
                "total_resource_slots": kp_policy.total_resource_slots.to_json(),
                "default_for_unspecified": str(kp_policy.default_for_unspecified),
            }

        result: CheckPresetsResult = await repository.check_presets(
            access_key=test_keypair_access_key,
            user_id=test_user_uuid,
            group_name=group_name,
            domain_name=test_domain_name,
            resource_policy=resource_policy_dict,
            scaling_group=test_scaling_group_name,
        )

        # Verify: Should use actual kernel occupied (3 CPU, 6GB) NOT cached (10 CPU, 20GB)
        # available (16 CPU, 32GB) - actual occupied (3 CPU, 6GB) = remaining (13 CPU, 26GB)
        sg_data = result.scaling_groups[test_scaling_group_name]
        assert sg_data.remaining["cpu"] == Decimal("13")
        assert sg_data.remaining["mem"] == Decimal("26624")
        assert sg_data.using["cpu"] == Decimal("3")
        assert sg_data.using["mem"] == Decimal("6144")

    async def test_non_alive_agents_excluded_from_remaining_calculation(
        self,
        repository: ResourcePresetRepository,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_name: str,
        test_user_uuid: uuid.UUID,
        test_keypair_access_key: AccessKey,
        test_resource_policy_dict: dict[str, str],
        alive_and_non_alive_agents: list[AgentId],
    ) -> None:
        """
        Test that non-ALIVE agents (LOST, TERMINATED, RESTARTING) are excluded
        from remaining resource calculation. Only ALIVE agents should contribute.
        """
        result: CheckPresetsResult = await repository.check_presets(
            access_key=test_keypair_access_key,
            user_id=test_user_uuid,
            group_name=test_group_name,
            domain_name=test_domain_name,
            resource_policy=test_resource_policy_dict,
            scaling_group=test_scaling_group_name,
        )

        # Verify: Only ALIVE agents (2 x 16 CPU, 2 x 32GB) should be counted
        # Non-ALIVE agents (3 x 100 CPU) should be excluded
        sg_data = result.scaling_groups[test_scaling_group_name]
        assert sg_data.remaining["cpu"] == Decimal("32")
        assert sg_data.remaining["mem"] == Decimal("65536")
