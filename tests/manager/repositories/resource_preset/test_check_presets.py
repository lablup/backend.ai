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

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

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
)
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_preset.db_source.db_source import (
    ResourcePresetDBSource,
)


class TestCheckPresetsOccupiedSlots:
    """
    Integration tests for check_presets verifying occupied slot calculation
    from actual kernel statuses (RUNNING, TERMINATING) instead of cached values.
    """

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans test data after each test"""
        yield database_engine

        # Cleanup all test data after test
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(KernelRow))
            await db_sess.execute(sa.delete(SessionRow))
            await db_sess.execute(sa.delete(AgentRow))
            await db_sess.execute(sa.delete(KeyPairRow))
            await db_sess.execute(sa.delete(UserRow))
            await db_sess.execute(sa.delete(GroupRow))
            await db_sess.execute(sa.delete(ScalingGroupRow))
            await db_sess.execute(sa.delete(DomainRow))
            await db_sess.execute(sa.delete(KeyPairResourcePolicyRow))
            await db_sess.execute(sa.delete(ProjectResourcePolicyRow))
            await db_sess.execute(sa.delete(UserResourcePolicyRow))

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

        try:
            yield group_id
        finally:
            # Cleanup handled by db_with_cleanup
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

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[AgentId, None]:
        """Create test agent and return agent ID"""
        agent_id = AgentId(f"agent-{uuid.uuid4().hex[:8]}")

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
                    "mem": Decimal("32768"),  # 32GB
                }),
                occupied_slots=ResourceSlot({  # Cached value - should be ignored
                    "cpu": Decimal("0"),
                    "mem": Decimal("0"),
                }),
                addr="10.0.0.1:2001",
                version="v25.03.0",  # Required NOT NULL field
                architecture="x86_64",
            )
            db_sess.add(agent)
            await db_sess.flush()

        try:
            yield agent_id
        finally:
            # Cleanup handled by db_with_cleanup
            pass

    @pytest.fixture
    def db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ResourcePresetDBSource:
        """Create ResourcePresetDBSource instance"""
        return ResourcePresetDBSource(db=db_with_cleanup)

    async def test_running_kernels_count_towards_occupied_slots(
        self,
        db_source: ResourcePresetDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair_access_key: AccessKey,
        test_agent_id: AgentId,
    ) -> None:
        """
        Test that RUNNING kernels contribute to occupied slots.
        Expected: available_slots - RUNNING kernel's occupied_slots
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

        # Test: get_agent_available_resources should calculate from kernel
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            known_slot_types: dict[SlotName, SlotTypes] = {
                SlotName("cpu"): SlotTypes("count"),
                SlotName("mem"): SlotTypes("bytes"),
            }
            per_sgroup_remaining, agent_slots = await db_source._get_agent_available_resources(
                db_sess,
                [test_scaling_group_name],
                known_slot_types,
            )

        # Verify: available (16 CPU, 32GB) - occupied (4 CPU, 8GB) = remaining (12 CPU, 24GB)
        assert per_sgroup_remaining[test_scaling_group_name]["cpu"] == Decimal("12")
        assert per_sgroup_remaining[test_scaling_group_name]["mem"] == Decimal("24576")

        assert len(agent_slots) == 1
        assert agent_slots[0]["cpu"] == Decimal("12")
        assert agent_slots[0]["mem"] == Decimal("24576")

    async def test_terminating_kernels_count_towards_occupied_slots(
        self,
        db_source: ResourcePresetDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair_access_key: AccessKey,
        test_agent_id: AgentId,
    ) -> None:
        """
        Test that TERMINATING kernels also contribute to occupied slots.
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

        # Test: get_agent_available_resources should include TERMINATING kernels
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            known_slot_types: dict[SlotName, SlotTypes] = {
                SlotName("cpu"): SlotTypes("count"),
                SlotName("mem"): SlotTypes("bytes"),
            }
            per_sgroup_remaining, agent_slots = await db_source._get_agent_available_resources(
                db_sess,
                [test_scaling_group_name],
                known_slot_types,
            )

        # Verify: available (16 CPU, 32GB) - occupied (2 CPU, 4GB) = remaining (14 CPU, 28GB)
        assert per_sgroup_remaining[test_scaling_group_name]["cpu"] == Decimal("14")
        assert per_sgroup_remaining[test_scaling_group_name]["mem"] == Decimal("28672")

        assert len(agent_slots) == 1
        assert agent_slots[0]["cpu"] == Decimal("14")
        assert agent_slots[0]["mem"] == Decimal("28672")

    async def test_pending_kernels_do_not_count_towards_occupied_slots(
        self,
        db_source: ResourcePresetDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair_access_key: AccessKey,
        test_agent_id: AgentId,
    ) -> None:
        """
        Test that PENDING kernels DO NOT contribute to occupied slots.
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

        # Test: get_agent_available_resources should ignore PENDING kernels
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            known_slot_types: dict[SlotName, SlotTypes] = {
                SlotName("cpu"): SlotTypes("count"),
                SlotName("mem"): SlotTypes("bytes"),
            }
            per_sgroup_remaining, agent_slots = await db_source._get_agent_available_resources(
                db_sess,
                [test_scaling_group_name],
                known_slot_types,
            )

        # Verify: available (16 CPU, 32GB) - occupied (0) = remaining (16 CPU, 32GB)
        assert per_sgroup_remaining[test_scaling_group_name]["cpu"] == Decimal("16")
        assert per_sgroup_remaining[test_scaling_group_name]["mem"] == Decimal("32768")

        assert len(agent_slots) == 1
        assert agent_slots[0]["cpu"] == Decimal("16")
        assert agent_slots[0]["mem"] == Decimal("32768")

    async def test_ignores_cached_occupied_slots_in_agent_row(
        self,
        db_source: ResourcePresetDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair_access_key: AccessKey,
    ) -> None:
        """
        Test that the method ignores AgentRow.occupied_slots (cached value)
        and calculates from actual kernel states even when cached value is wrong.
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

        # Test: should use ACTUAL kernel occupied slots, not cached agent value
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            known_slot_types: dict[SlotName, SlotTypes] = {
                SlotName("cpu"): SlotTypes("count"),
                SlotName("mem"): SlotTypes("bytes"),
            }
            per_sgroup_remaining, agent_slots = await db_source._get_agent_available_resources(
                db_sess,
                [test_scaling_group_name],
                known_slot_types,
            )

        # Verify: Should use actual kernel occupied (3 CPU, 6GB) NOT cached (10 CPU, 20GB)
        # available (16 CPU, 32GB) - actual occupied (3 CPU, 6GB) = remaining (13 CPU, 26GB)
        assert per_sgroup_remaining[test_scaling_group_name]["cpu"] == Decimal("13")
        assert per_sgroup_remaining[test_scaling_group_name]["mem"] == Decimal("26624")

        # Should have 1 agent (only the agent with wrong cache that has a kernel)
        assert len(agent_slots) == 1

        # Verify the agent with wrong cache has correct remaining slots
        assert agent_slots[0]["cpu"] == Decimal("13")
        assert agent_slots[0]["mem"] == Decimal("26624")
