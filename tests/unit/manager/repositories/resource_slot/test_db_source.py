"""Integration tests for ResourceSlotDBSource with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import ResourceSlot, SlotName
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.errors.resource_slot import (
    ResourceSlotTypeNotFound,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
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

    async def test_get_slot_type_found(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        slot_type = await db_source.get_slot_type("cpu")
        assert slot_type.slot_name == "cpu"
        assert slot_type.slot_type == "count"

    async def test_get_slot_type_not_found(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        with pytest.raises(ResourceSlotTypeNotFound):
            await db_source.get_slot_type("nonexistent")


class TestComputeActualAgentResourceUsage:
    """Tests for compute_actual_agent_resource_usage."""

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
                ScalingGroupRow,
                GroupRow,
                AgentRow,
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

    async def _seed_infrastructure(self, db: ExtendedAsyncSAEngine) -> tuple[str, uuid.UUID, str]:
        """Create domain, project, scaling group, and agent."""
        domain_name = "test-domain"
        project_id = uuid4()
        sg_name = "test-sg"
        agent_id = "i-test-agent"
        async with db.begin_session() as db_sess:
            db_sess.add(DomainRow(name=domain_name))
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
                ScalingGroupRow(
                    name=sg_name,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
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
                    available_slots=ResourceSlot({SlotName("cpu"): "8"}),
                    occupied_slots=ResourceSlot({}),
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
        status: KernelStatus,
        allocations: dict[str, tuple[Decimal, Decimal | None]],
        free_at: datetime | None = None,
    ) -> uuid.UUID:
        session_id = uuid4()
        kernel_id = uuid4()
        empty_slots = ResourceSlot({})
        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    domain_name=domain_name,
                    group_id=project_id,
                    user_uuid=uuid4(),
                    occupying_slots=empty_slots,
                    requested_slots=empty_slots,
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
                    occupied_slots=empty_slots,
                    requested_slots=empty_slots,
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    scaling_group="test-sg",
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
    ) -> None:
        """Active allocations are summed per (agent_id, slot_name)."""
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(db)

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
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
    ) -> None:
        """Allocations with free_at set are excluded."""
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(db)

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
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
    ) -> None:
        """Kernels with TERMINATED status are excluded."""
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(db)

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            status=KernelStatus.TERMINATED,
            allocations={"cpu": (Decimal("4"), Decimal("4"))},
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.compute_actual_agent_resource_usage()

        assert result == {}

    async def test_coalesce_uses_requested_when_used_is_none(
        self,
        db_with_full_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """When used is None, COALESCE falls back to requested."""
        db = db_with_full_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(db)

        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            status=KernelStatus.SCHEDULED,
            allocations={"cpu": (Decimal("4"), None)},
        )

        db_source = ResourceSlotDBSource(db)
        result = await db_source.compute_actual_agent_resource_usage()

        assert result[(agent_id, "cpu")] == Decimal("4")
