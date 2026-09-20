"""Integration tests for ResourceSlotDBSource with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import (
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_slot.db_source import ResourceSlotDBSource
from ai.backend.testutils.db import with_tables


class TestSlotTypes:
    """Tests for resource_slot_types read operations."""

    async def test_all_slot_types(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        types = await db_source.all_slot_types()
        assert len(types) == 2
        names = [t.slot_name for t in types]
        assert "cpu" in names
        assert "mem" in names


class TestAggregation:
    """Tests for aggregate_occupied_by_domain and aggregate_occupied_by_project."""

    @pytest.fixture
    def domain_id(self) -> DomainID:
        return DomainID(uuid4())

    @pytest.fixture
    def resource_group_id(self) -> ResourceGroupID:
        return ResourceGroupID(uuid4())

    @pytest.fixture
    async def db_with_full_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                UserRow,
                ProjectRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    async def _seed_slot_types(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count", rank=0))
            db_sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes", rank=1))

    async def _seed_infrastructure(
        self,
        db: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> tuple[str, uuid.UUID, str]:
        """Create domain, project, scaling group, and agent. Returns (domain_name, project_id, agent_id)."""
        domain_name = "test-domain"
        project_id = uuid4()
        sg_name = "test-sg"
        agent_id = "i-test-agent"
        async with db.begin_session() as db_sess:
            db_sess.add(DomainRow(id=domain_id, name=domain_name))
        async with db.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=0,
                    max_network_count=5,
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name=sg_name,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name="test-project",
                    domain_name=domain_name,
                    resource_policy="default",
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=AgentStatus.ALIVE,
                    status_changed=datetime.now(tzutc()),
                    region="test-region",
                    scaling_group=sg_name,
                    resource_group_id=resource_group_id,
                    addr="tcp://127.0.0.1:6001",
                    version="24.12.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )
        return domain_name, project_id, agent_id

    async def _create_kernel_with_allocations(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        project_id: uuid.UUID,
        agent_id: str,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
        status: KernelStatus,
        allocations: dict[str, tuple[Decimal, Decimal | None]],
        free_at: datetime | None = None,
    ) -> uuid.UUID:
        """Create a session + kernel + resource allocations.

        Args:
            allocations: mapping of slot_name → (requested, used).
        """
        session_id = uuid4()
        kernel_id = uuid4()
        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    domain_id=domain_id,
                    domain_name=domain_name,
                    group_id=project_id,
                    resource_group_id=resource_group_id,
                    scaling_group_name="test-sg",
                    user_uuid=uuid4(),
                )
            )
            await db_sess.flush()
            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=project_id,
                    user_uuid=uuid4(),
                    status=status,
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    scaling_group="test-sg",
                    resource_group_id=resource_group_id,
                    agent=agent_id,
                )
            )
            await db_sess.flush()
            for slot_name, (requested, used) in allocations.items():
                db_sess.add(
                    ResourceAllocationRow(
                        kernel_id=kernel_id,
                        slot_name=slot_name,
                        requested=requested,
                        used=used,
                        free_at=free_at,
                    )
                )
        return kernel_id

    async def test_aggregate_by_domain_with_active_kernels(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(
            db, domain_id, resource_group_id
        )

        # Kernel 1: RUNNING with used values
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.RUNNING,
            allocations={
                "cpu": (Decimal("2"), Decimal("2")),
                "mem": (Decimal("1024"), Decimal("1024")),
            },
        )
        # Kernel 2: SCHEDULED with only requested (used=None)
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.SCHEDULED,
            allocations={
                "cpu": (Decimal("4"), None),
                "mem": (Decimal("2048"), None),
            },
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.aggregate_occupied_by_domain(domain_name)

        assert result.session_count == 2
        by_slot = {sq.slot_name: sq.quantity for sq in result.used_slots}
        # RUNNING: COALESCE(used=2, requested=2)=2, SCHEDULED: COALESCE(used=NULL, requested=4)=4
        assert by_slot["cpu"] == Decimal("6")
        # RUNNING: 1024, SCHEDULED: 2048
        assert by_slot["mem"] == Decimal("3072")

    async def test_aggregate_by_domain_excludes_terminated_kernels(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(
            db, domain_id, resource_group_id
        )

        # TERMINATED kernel — should be excluded
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.TERMINATED,
            allocations={"cpu": (Decimal("4"), Decimal("4"))},
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.aggregate_occupied_by_domain(domain_name)

        assert result.session_count == 0
        assert result.used_slots == []

    async def test_aggregate_by_domain_excludes_freed_allocations(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(
            db, domain_id, resource_group_id
        )

        # RUNNING kernel but allocations already freed (free_at is set)
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.RUNNING,
            allocations={"cpu": (Decimal("2"), Decimal("2"))},
            free_at=datetime.now(tzutc()),
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.aggregate_occupied_by_domain(domain_name)

        assert result.session_count == 0
        assert result.used_slots == []

    async def test_aggregate_by_domain_empty(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
    ) -> None:
        db = db_with_full_tables
        await self._seed_slot_types(db)
        db_source = ResourceSlotDBSource(db)

        result = await db_source.aggregate_occupied_by_domain("nonexistent-domain")

        assert result.session_count == 0
        assert result.used_slots == []

    async def test_aggregate_by_project_with_active_kernels(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(
            db, domain_id, resource_group_id
        )

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.RUNNING,
            allocations={
                "cpu": (Decimal("1"), Decimal("1")),
                "mem": (Decimal("512"), Decimal("512")),
            },
        )
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.PREPARING,
            allocations={
                "cpu": (Decimal("3"), None),
                "mem": (Decimal("1536"), None),
            },
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.aggregate_occupied_by_project(project_id)

        assert result.session_count == 2
        by_slot = {sq.slot_name: sq.quantity for sq in result.used_slots}
        assert by_slot["cpu"] == Decimal("4")
        assert by_slot["mem"] == Decimal("2048")

    async def test_aggregate_by_project_empty(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
    ) -> None:
        db = db_with_full_tables
        await self._seed_slot_types(db)
        db_source = ResourceSlotDBSource(db)

        result = await db_source.aggregate_occupied_by_project(uuid4())

        assert result.session_count == 0
        assert result.used_slots == []

    async def test_aggregate_slots_sorted_by_rank(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        """Verify used_slots are sorted by rank (cpu=0 before mem=1)."""
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(
            db, domain_id, resource_group_id
        )

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.RUNNING,
            allocations={
                "cpu": (Decimal("1"), Decimal("1")),
                "mem": (Decimal("1024"), Decimal("1024")),
            },
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.aggregate_occupied_by_domain(domain_name)

        assert len(result.used_slots) == 2
        assert result.used_slots[0].slot_name == "cpu"
        assert result.used_slots[1].slot_name == "mem"


class TestComputeActualAgentResourceUsage:
    """Tests for compute_actual_agent_resource_usage."""

    @pytest.fixture
    def domain_id(self) -> DomainID:
        return DomainID(uuid4())

    @pytest.fixture
    def resource_group_id(self) -> ResourceGroupID:
        return ResourceGroupID(uuid4())

    @pytest.fixture
    async def db_with_full_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                UserRow,
                ProjectRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    async def _seed_slot_types(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count", rank=0))
            db_sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes", rank=1))

    async def _seed_infrastructure(
        self,
        db: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> tuple[str, uuid.UUID, str]:
        """Create domain, project, scaling group, and agent."""
        domain_name = "test-domain"
        project_id = uuid4()
        sg_name = "test-sg"
        agent_id = "i-test-agent"
        async with db.begin_session() as db_sess:
            db_sess.add(DomainRow(id=domain_id, name=domain_name))
        async with db.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=0,
                    max_network_count=5,
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name=sg_name,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name="test-project",
                    domain_name=domain_name,
                    resource_policy="default",
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=AgentStatus.ALIVE,
                    status_changed=datetime.now(tzutc()),
                    region="test-region",
                    scaling_group=sg_name,
                    resource_group_id=resource_group_id,
                    addr="tcp://127.0.0.1:6001",
                    version="24.12.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )
        return domain_name, project_id, agent_id

    async def _create_kernel_with_allocations(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        project_id: uuid.UUID,
        agent_id: str,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
        status: KernelStatus,
        allocations: dict[str, tuple[Decimal, Decimal | None]],
        free_at: datetime | None = None,
    ) -> uuid.UUID:
        session_id = uuid4()
        kernel_id = uuid4()
        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    domain_id=domain_id,
                    domain_name=domain_name,
                    group_id=project_id,
                    resource_group_id=resource_group_id,
                    scaling_group_name="test-sg",
                    user_uuid=uuid4(),
                )
            )
            await db_sess.flush()
            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=project_id,
                    user_uuid=uuid4(),
                    status=status,
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    scaling_group="test-sg",
                    resource_group_id=resource_group_id,
                    agent=agent_id,
                )
            )
            await db_sess.flush()
            for slot_name, (requested, used) in allocations.items():
                db_sess.add(
                    ResourceAllocationRow(
                        kernel_id=kernel_id,
                        slot_name=slot_name,
                        requested=requested,
                        used=used,
                        free_at=free_at,
                    )
                )
        return kernel_id

    async def test_no_active_allocations(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """Returns empty dict when there are no active allocations."""
        db = db_with_full_tables
        await self._seed_slot_types(db)

        db_source = ResourceSlotDBSource(db)
        result = await db_source.compute_actual_agent_resource_usage()

        assert result == {}

    async def test_active_allocations_summed_by_agent_and_slot(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        """Active allocations are summed per (agent_id, slot_name)."""
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(
            db, domain_id, resource_group_id
        )

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.RUNNING,
            allocations={
                "cpu": (Decimal("2"), Decimal("2")),
                "mem": (Decimal("1024"), Decimal("1024")),
            },
        )
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.RUNNING,
            allocations={
                "cpu": (Decimal("4"), Decimal("4")),
                "mem": (Decimal("2048"), Decimal("2048")),
            },
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.compute_actual_agent_resource_usage()

        assert result[(agent_id, "cpu")] == Decimal("6")
        assert result[(agent_id, "mem")] == Decimal("3072")

    async def test_freed_allocations_excluded(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        """Allocations with free_at set are excluded."""
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(
            db, domain_id, resource_group_id
        )

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.RUNNING,
            allocations={"cpu": (Decimal("4"), Decimal("4"))},
            free_at=datetime.now(tzutc()),
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.compute_actual_agent_resource_usage()

        assert result == {}

    async def test_terminated_kernels_excluded(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        """Kernels with TERMINATED status are excluded."""
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(
            db, domain_id, resource_group_id
        )

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.TERMINATED,
            allocations={"cpu": (Decimal("4"), Decimal("4"))},
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.compute_actual_agent_resource_usage()

        assert result == {}

    async def test_coalesce_uses_requested_when_used_is_none(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        """When used is None, COALESCE falls back to requested."""
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(
            db, domain_id, resource_group_id
        )

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            status=KernelStatus.SCHEDULED,
            allocations={"cpu": (Decimal("4"), None)},
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.compute_actual_agent_resource_usage()

        assert result[(agent_id, "cpu")] == Decimal("4")
