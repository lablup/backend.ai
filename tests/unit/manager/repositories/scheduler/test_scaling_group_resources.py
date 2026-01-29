"""
Tests for calculate_total_resource_slots_by_scaling_group method in ScheduleDBSource.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.db import with_tables

# =============================================================================
# Data classes for test configuration
# =============================================================================


@dataclass
class UserFixtureData:
    user_uuid: uuid.UUID
    access_key: str
    domain_name: str


@dataclass
class AgentConfig:
    """Configuration for creating an agent."""

    available_slots: ResourceSlot
    status: AgentStatus = AgentStatus.ALIVE
    schedulable: bool = True


@dataclass
class KernelConfig:
    """Configuration for creating a kernel on a specific agent."""

    agent_idx: int
    occupied_slots: ResourceSlot
    status: KernelStatus = KernelStatus.RUNNING


@dataclass
class ScenarioConfig:
    """Configuration for building a test scenario via indirect parametrize."""

    name: str
    agents: list[AgentConfig]
    kernels: list[KernelConfig] = field(default_factory=list)
    expected_capacity: ResourceSlot = field(default_factory=lambda: ResourceSlot({}))
    expected_used: ResourceSlot = field(default_factory=lambda: ResourceSlot({}))
    expected_free: ResourceSlot = field(default_factory=lambda: ResourceSlot({}))


@dataclass
class ResourceTestScenario:
    """Complete test scenario with db_source and expected results."""

    db_source: ScheduleDBSource
    scaling_group_name: str
    expected_capacity: ResourceSlot
    expected_used: ResourceSlot
    expected_free: ResourceSlot


# =============================================================================
# Test class
# =============================================================================


class TestCalculateTotalResourceSlotsByScalingGroup:
    """Tests for calculate_total_resource_slots_by_scaling_group method."""

    # =========================================================================
    # Base fixtures (randomized for parallel test support)
    # =========================================================================

    @pytest.fixture
    def domain_name(self) -> str:
        return f"domain-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def policy_name(self) -> str:
        return f"policy-{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database with required tables for testing."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ImageRow,
                SessionRow,
                AgentRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def domain_row(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        domain_name: str,
    ) -> str:
        """Create domain and return domain_name."""
        async with db_with_tables.begin_session() as sess:
            sess.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots={},
                )
            )
            await sess.flush()
        return domain_name

    @pytest.fixture
    async def resource_policies(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        policy_name: str,
    ) -> str:
        """Create resource policies and return policy_name."""
        async with db_with_tables.begin_session() as sess:
            sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            sess.add(
                KeyPairResourcePolicyRow(
                    name=policy_name,
                    total_resource_slots=ResourceSlot({"cpu": Decimal("100")}),
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_pending_session_count=5,
                    max_pending_session_resource_slots=ResourceSlot({}),
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            await sess.flush()
        return policy_name

    @pytest.fixture
    async def user_fixture_data(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        domain_row: str,
        resource_policies: str,
    ) -> UserFixtureData:
        """Create user and keypair, return UserFixtureData."""
        user_uuid = uuid.uuid4()
        access_key = f"AKTEST{uuid.uuid4().hex[:12].upper()}"

        async with db_with_tables.begin_session() as sess:
            password_info = PasswordInfo(
                password="dummy",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=600_000,
                salt_size=32,
            )
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=password_info,
                domain_name=domain_row,
                role=UserRole.USER,
                resource_policy=resource_policies,
            )
            sess.add(user)
            await sess.flush()

            sess.add(
                KeyPairRow(
                    access_key=AccessKey(access_key),
                    secret_key="dummy-secret",
                    user_id=user.email,
                    user=user.uuid,
                    is_active=True,
                    resource_policy=resource_policies,
                )
            )
            await sess.flush()

        return UserFixtureData(
            user_uuid=user_uuid,
            access_key=access_key,
            domain_name=domain_row,
        )

    @pytest.fixture
    async def group_id(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        domain_row: str,
        resource_policies: str,
    ) -> uuid.UUID:
        """Create group and return group_id."""
        gid = uuid.uuid4()
        async with db_with_tables.begin_session() as sess:
            sess.add(
                GroupRow(
                    id=gid,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_row,
                    total_resource_slots=ResourceSlot({}),
                    resource_policy=resource_policies,
                )
            )
            await sess.flush()
        return gid

    # =========================================================================
    # Helper methods for fixture setup
    # =========================================================================

    async def _create_scaling_group(
        self, db: ExtendedAsyncSAEngine, name: str | None = None
    ) -> str:
        """Create a scaling group and return its name."""
        sg_name = name or f"sg-{uuid.uuid4().hex[:8]}"
        async with db.begin_session() as sess:
            sess.add(
                ScalingGroupRow(
                    name=sg_name,
                    description=f"Test scaling group {sg_name}",
                    is_active=True,
                    is_public=True,
                    driver="static",
                    scheduler="fifo",
                    driver_opts={},
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            await sess.flush()
        return sg_name

    async def _create_agent(
        self,
        db: ExtendedAsyncSAEngine,
        scaling_group_name: str,
        config: AgentConfig,
    ) -> str:
        """Create an agent and return its ID."""
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        async with db.begin_session() as sess:
            sess.add(
                AgentRow(
                    id=AgentId(agent_id),
                    status=config.status,
                    region="local",
                    scaling_group=scaling_group_name,
                    available_slots=config.available_slots,
                    occupied_slots=ResourceSlot({}),
                    addr=f"tcp://127.0.0.1:{5000 + hash(agent_id) % 1000}",
                    first_contact=datetime.now(UTC),
                    lost_at=None,
                    version="24.03.0",
                    architecture="x86_64",
                    compute_plugins={},
                    schedulable=config.schedulable,
                )
            )
            await sess.flush()
        return agent_id

    async def _create_kernel_with_session(
        self,
        db: ExtendedAsyncSAEngine,
        agent_id: str,
        scaling_group_name: str,
        user_data: UserFixtureData,
        group_id: uuid.UUID,
        config: KernelConfig,
    ) -> None:
        """Create a kernel with its session."""
        session_id = SessionId(uuid.uuid4())
        kernel_id = uuid.uuid4()

        async with db.begin_session() as sess:
            sess.add(
                SessionRow(
                    id=session_id,
                    name=f"session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=user_data.domain_name,
                    group_id=group_id,
                    user_uuid=user_data.user_uuid,
                    access_key=AccessKey(user_data.access_key),
                    scaling_group_name=scaling_group_name,
                    status=SessionStatus.RUNNING,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=config.occupied_slots,
                    created_at=datetime.now(tzutc()),
                    images=["python:3.8"],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                )
            )
            await sess.flush()

            sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    access_key=AccessKey(user_data.access_key),
                    agent=AgentId(agent_id),
                    agent_addr="tcp://127.0.0.1:5001",
                    scaling_group=scaling_group_name,
                    cluster_idx=0,
                    cluster_role="main",
                    cluster_hostname="kernel-0",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    status=config.status,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=config.occupied_slots,
                    requested_slots=config.occupied_slots,
                    domain_name=user_data.domain_name,
                    group_id=group_id,
                    user_uuid=user_data.user_uuid,
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2001,
                    repl_out_port=2002,
                    stdin_port=2003,
                    stdout_port=2004,
                )
            )
            await sess.flush()

    # =========================================================================
    # Indirect parametrize fixture
    # =========================================================================

    @pytest.fixture
    async def resource_test_scenario(
        self,
        request: pytest.FixtureRequest,
        db_with_tables: ExtendedAsyncSAEngine,
        user_fixture_data: UserFixtureData,
        group_id: uuid.UUID,
    ) -> ResourceTestScenario:
        """Build a test scenario from ScenarioConfig via indirect parametrize."""
        config: ScenarioConfig = request.param

        sg_name = await self._create_scaling_group(db_with_tables)

        agent_ids: list[str] = []
        for agent_config in config.agents:
            agent_id = await self._create_agent(db_with_tables, sg_name, agent_config)
            agent_ids.append(agent_id)

        for kernel_config in config.kernels:
            await self._create_kernel_with_session(
                db_with_tables,
                agent_ids[kernel_config.agent_idx],
                sg_name,
                user_fixture_data,
                group_id,
                kernel_config,
            )

        return ResourceTestScenario(
            db_source=ScheduleDBSource(db_with_tables),
            scaling_group_name=sg_name,
            expected_capacity=config.expected_capacity,
            expected_used=config.expected_used,
            expected_free=config.expected_free,
        )

    # =========================================================================
    # Single agent resource calculation tests
    # =========================================================================

    @pytest.mark.parametrize(
        "resource_test_scenario",
        [
            ScenarioConfig(
                name="no_kernel",
                agents=[
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("4"),
                            "mem": Decimal("8589934592"),
                        })
                    )
                ],
                kernels=[],
                expected_capacity=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
                expected_used=ResourceSlot({}),
                expected_free=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
            ),
            ScenarioConfig(
                name="partial_usage",
                agents=[
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("4"),
                            "mem": Decimal("8589934592"),
                        })
                    )
                ],
                kernels=[
                    KernelConfig(
                        agent_idx=0,
                        occupied_slots=ResourceSlot({
                            "cpu": Decimal("1"),
                            "mem": Decimal("2147483648"),
                        }),
                    )
                ],
                expected_capacity=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
                expected_used=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2147483648")}),
                expected_free=ResourceSlot({"cpu": Decimal("3"), "mem": Decimal("6442450944")}),
            ),
            ScenarioConfig(
                name="full_usage",
                agents=[
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("4"),
                            "mem": Decimal("8589934592"),
                        })
                    )
                ],
                kernels=[
                    KernelConfig(
                        agent_idx=0,
                        occupied_slots=ResourceSlot({
                            "cpu": Decimal("4"),
                            "mem": Decimal("8589934592"),
                        }),
                    )
                ],
                expected_capacity=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
                expected_used=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
                expected_free=ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
            ),
            ScenarioConfig(
                name="with_gpu",
                agents=[
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("8"),
                            "mem": Decimal("17179869184"),
                            "cuda.shares": Decimal("4"),
                        })
                    )
                ],
                kernels=[
                    KernelConfig(
                        agent_idx=0,
                        occupied_slots=ResourceSlot({
                            "cpu": Decimal("2"),
                            "mem": Decimal("4294967296"),
                            "cuda.shares": Decimal("1"),
                        }),
                    )
                ],
                expected_capacity=ResourceSlot({
                    "cpu": Decimal("8"),
                    "mem": Decimal("17179869184"),
                    "cuda.shares": Decimal("4"),
                }),
                expected_used=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4294967296"),
                    "cuda.shares": Decimal("1"),
                }),
                expected_free=ResourceSlot({
                    "cpu": Decimal("6"),
                    "mem": Decimal("12884901888"),
                    "cuda.shares": Decimal("3"),
                }),
            ),
        ],
        indirect=True,
        ids=lambda c: c.name,
    )
    @pytest.mark.asyncio
    async def test_single_agent_resource_calculation(
        self, resource_test_scenario: ResourceTestScenario
    ) -> None:
        """Test resource calculation for single agent scenarios."""
        result = (
            await resource_test_scenario.db_source.calculate_total_resource_slots_by_scaling_group(
                resource_test_scenario.scaling_group_name
            )
        )

        assert result.total_capacity_slots == resource_test_scenario.expected_capacity
        assert result.total_used_slots == resource_test_scenario.expected_used
        assert result.total_free_slots == resource_test_scenario.expected_free

    # =========================================================================
    # Multi-agent resource aggregation tests
    # =========================================================================

    @pytest.mark.parametrize(
        "resource_test_scenario",
        [
            ScenarioConfig(
                name="two_agents_no_kernels",
                agents=[
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("4"),
                            "mem": Decimal("8589934592"),
                        })
                    ),
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("8"),
                            "mem": Decimal("17179869184"),
                        })
                    ),
                ],
                kernels=[],
                expected_capacity=ResourceSlot({
                    "cpu": Decimal("12"),
                    "mem": Decimal("25769803776"),
                }),
                expected_used=ResourceSlot({}),
                expected_free=ResourceSlot({"cpu": Decimal("12"), "mem": Decimal("25769803776")}),
            ),
            ScenarioConfig(
                name="two_agents_one_kernel",
                agents=[
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("4"),
                            "mem": Decimal("8589934592"),
                        })
                    ),
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("8"),
                            "mem": Decimal("17179869184"),
                        })
                    ),
                ],
                kernels=[
                    KernelConfig(
                        agent_idx=0,
                        occupied_slots=ResourceSlot({
                            "cpu": Decimal("2"),
                            "mem": Decimal("4294967296"),
                        }),
                    )
                ],
                expected_capacity=ResourceSlot({
                    "cpu": Decimal("12"),
                    "mem": Decimal("25769803776"),
                }),
                expected_used=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
                expected_free=ResourceSlot({"cpu": Decimal("10"), "mem": Decimal("21474836480")}),
            ),
            ScenarioConfig(
                name="two_agents_two_kernels",
                agents=[
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("4"),
                            "mem": Decimal("8589934592"),
                        })
                    ),
                    AgentConfig(
                        available_slots=ResourceSlot({
                            "cpu": Decimal("8"),
                            "mem": Decimal("17179869184"),
                        })
                    ),
                ],
                kernels=[
                    KernelConfig(
                        agent_idx=0,
                        occupied_slots=ResourceSlot({
                            "cpu": Decimal("2"),
                            "mem": Decimal("2147483648"),
                        }),
                    ),
                    KernelConfig(
                        agent_idx=1,
                        occupied_slots=ResourceSlot({
                            "cpu": Decimal("3"),
                            "mem": Decimal("4294967296"),
                        }),
                    ),
                ],
                expected_capacity=ResourceSlot({
                    "cpu": Decimal("12"),
                    "mem": Decimal("25769803776"),
                }),
                expected_used=ResourceSlot({"cpu": Decimal("5"), "mem": Decimal("6442450944")}),
                expected_free=ResourceSlot({"cpu": Decimal("7"), "mem": Decimal("19327352832")}),
            ),
            ScenarioConfig(
                name="multiple_kernels_per_agent",
                agents=[
                    AgentConfig(available_slots=ResourceSlot({"cpu": Decimal("4")})),
                    AgentConfig(available_slots=ResourceSlot({"cpu": Decimal("4")})),
                    AgentConfig(available_slots=ResourceSlot({"cpu": Decimal("4")})),
                ],
                kernels=[
                    KernelConfig(agent_idx=0, occupied_slots=ResourceSlot({"cpu": Decimal("1")})),
                    KernelConfig(agent_idx=0, occupied_slots=ResourceSlot({"cpu": Decimal("2")})),
                    KernelConfig(agent_idx=2, occupied_slots=ResourceSlot({"cpu": Decimal("3")})),
                ],
                expected_capacity=ResourceSlot({"cpu": Decimal("12")}),
                expected_used=ResourceSlot({"cpu": Decimal("6")}),
                expected_free=ResourceSlot({"cpu": Decimal("6")}),
            ),
        ],
        indirect=True,
        ids=lambda c: c.name,
    )
    @pytest.mark.asyncio
    async def test_multi_agent_resource_aggregation(
        self, resource_test_scenario: ResourceTestScenario
    ) -> None:
        """Test resource aggregation for multi-agent scenarios."""
        result = (
            await resource_test_scenario.db_source.calculate_total_resource_slots_by_scaling_group(
                resource_test_scenario.scaling_group_name
            )
        )

        assert result.total_capacity_slots == resource_test_scenario.expected_capacity
        assert result.total_used_slots == resource_test_scenario.expected_used
        assert result.total_free_slots == resource_test_scenario.expected_free

    # =========================================================================
    # Kernel status filtering tests
    # =========================================================================

    @pytest.mark.parametrize(
        "resource_test_scenario",
        [
            ScenarioConfig(
                name="terminated_kernel_excluded",
                agents=[AgentConfig(available_slots=ResourceSlot({"cpu": Decimal("4")}))],
                kernels=[
                    KernelConfig(
                        agent_idx=0,
                        occupied_slots=ResourceSlot({"cpu": Decimal("2")}),
                        status=KernelStatus.TERMINATED,
                    )
                ],
                expected_capacity=ResourceSlot({"cpu": Decimal("4")}),
                expected_used=ResourceSlot({}),
                expected_free=ResourceSlot({"cpu": Decimal("4")}),
            ),
            ScenarioConfig(
                name="running_kernel_counted",
                agents=[AgentConfig(available_slots=ResourceSlot({"cpu": Decimal("4")}))],
                kernels=[
                    KernelConfig(
                        agent_idx=0,
                        occupied_slots=ResourceSlot({"cpu": Decimal("2")}),
                        status=KernelStatus.RUNNING,
                    )
                ],
                expected_capacity=ResourceSlot({"cpu": Decimal("4")}),
                expected_used=ResourceSlot({"cpu": Decimal("2")}),
                expected_free=ResourceSlot({"cpu": Decimal("2")}),
            ),
            ScenarioConfig(
                name="terminating_kernel_counted",
                agents=[AgentConfig(available_slots=ResourceSlot({"cpu": Decimal("4")}))],
                kernels=[
                    KernelConfig(
                        agent_idx=0,
                        occupied_slots=ResourceSlot({"cpu": Decimal("2")}),
                        status=KernelStatus.TERMINATING,
                    )
                ],
                expected_capacity=ResourceSlot({"cpu": Decimal("4")}),
                expected_used=ResourceSlot({"cpu": Decimal("2")}),
                expected_free=ResourceSlot({"cpu": Decimal("2")}),
            ),
        ],
        indirect=True,
        ids=lambda c: c.name,
    )
    @pytest.mark.asyncio
    async def test_kernel_status_filtering(
        self, resource_test_scenario: ResourceTestScenario
    ) -> None:
        """Test that kernel status affects occupied slot calculation."""
        result = (
            await resource_test_scenario.db_source.calculate_total_resource_slots_by_scaling_group(
                resource_test_scenario.scaling_group_name
            )
        )

        assert result.total_capacity_slots == resource_test_scenario.expected_capacity
        assert result.total_used_slots == resource_test_scenario.expected_used
        assert result.total_free_slots == resource_test_scenario.expected_free

    # =========================================================================
    # Agent filtering tests
    # =========================================================================

    @pytest.mark.parametrize(
        "resource_test_scenario",
        [
            ScenarioConfig(
                name="excludes_terminated_agent",
                agents=[
                    AgentConfig(available_slots=ResourceSlot({"cpu": Decimal("4")})),
                    AgentConfig(
                        available_slots=ResourceSlot({"cpu": Decimal("8")}),
                        status=AgentStatus.TERMINATED,
                    ),
                ],
                kernels=[],
                expected_capacity=ResourceSlot({"cpu": Decimal("4")}),
                expected_used=ResourceSlot({}),
                expected_free=ResourceSlot({"cpu": Decimal("4")}),
            ),
            ScenarioConfig(
                name="excludes_non_schedulable_agent",
                agents=[
                    AgentConfig(available_slots=ResourceSlot({"cpu": Decimal("4")})),
                    AgentConfig(
                        available_slots=ResourceSlot({"cpu": Decimal("8")}),
                        schedulable=False,
                    ),
                ],
                kernels=[],
                expected_capacity=ResourceSlot({"cpu": Decimal("4")}),
                expected_used=ResourceSlot({}),
                expected_free=ResourceSlot({"cpu": Decimal("4")}),
            ),
        ],
        indirect=True,
        ids=lambda c: c.name,
    )
    @pytest.mark.asyncio
    async def test_agent_filtering(self, resource_test_scenario: ResourceTestScenario) -> None:
        """Test that terminated and non-schedulable agents are excluded."""
        result = (
            await resource_test_scenario.db_source.calculate_total_resource_slots_by_scaling_group(
                resource_test_scenario.scaling_group_name
            )
        )

        assert result.total_capacity_slots == resource_test_scenario.expected_capacity
        assert result.total_used_slots == resource_test_scenario.expected_used
        assert result.total_free_slots == resource_test_scenario.expected_free

    @pytest.fixture
    def db_source_only(self, db_with_tables: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        """Create ScheduleDBSource for nonexistent scaling group test."""
        return ScheduleDBSource(db_with_tables)

    @pytest.mark.asyncio
    async def test_returns_empty_slots_for_nonexistent_scaling_group(
        self, db_source_only: ScheduleDBSource
    ) -> None:
        """Test that empty slots are returned for non-existent scaling group."""
        result = await db_source_only.calculate_total_resource_slots_by_scaling_group(
            "nonexistent-sg"
        )

        assert len(result.total_capacity_slots) == 0
        assert len(result.total_used_slots) == 0
        assert len(result.total_free_slots) == 0
