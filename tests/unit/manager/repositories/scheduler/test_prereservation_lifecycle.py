"""Full-lifecycle tests for preemption reservations (BA-6748).

Covers the ``prereserved`` ledger across both tables:
reserve_sessions (PENDING -> RESERVED, prereserved hold) ->
admit_prereserved_kernels (prereserved -> reserved, kernel SCHEDULED) ->
RUNNING activation (reserved -> used) -> free (all buckets zero), with the
``agent counter == sum of row buckets`` invariant checked at every step,
plus the cancel-while-RESERVED release path and the capacity guards.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey, AgentId, KernelId, ResourceSlot, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_slot import ResourceAllocationRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource

from .conftest import (
    create_pending_session_with_kernels,
    fetch_agent_resources,
    make_session_allocations,
    seed_agent_resources,
)


async def _assert_ledger_invariant(
    db: ExtendedAsyncSAEngine,
    agent_id: str,
    seeded_used: Mapping[str, Decimal] = {},
) -> None:
    """agent counters must equal the sum of the active rows' buckets.

    ``seeded_used`` is the victims' usage the test seeded directly on the
    agent (without allocation rows).
    """
    async with db.begin_readonly_session() as db_sess:
        row_sums = {
            row.slot_name: row
            for row in (
                await db_sess.execute(
                    sa.select(
                        ResourceAllocationRow.slot_name,
                        sa.func.coalesce(sa.func.sum(ResourceAllocationRow.prereserved), 0).label(
                            "prereserved"
                        ),
                        sa.func.coalesce(sa.func.sum(ResourceAllocationRow.reserved), 0).label(
                            "reserved"
                        ),
                        sa.func.coalesce(sa.func.sum(ResourceAllocationRow.used), 0).label("used"),
                    )
                    .select_from(
                        ResourceAllocationRow.__table__.join(
                            KernelRow.__table__,
                            KernelRow.id == ResourceAllocationRow.kernel_id,
                        )
                    )
                    .where(
                        KernelRow.agent == agent_id,
                        ResourceAllocationRow.free_at.is_(None),
                    )
                    .group_by(ResourceAllocationRow.slot_name)
                )
            ).all()
        }
    agent_rows = await fetch_agent_resources(db, agent_id)
    for slot_name, agent_row in agent_rows.items():
        sums = row_sums.get(slot_name)
        prereserved = sums.prereserved if sums is not None else Decimal(0)
        reserved = sums.reserved if sums is not None else Decimal(0)
        used = sums.used if sums is not None else Decimal(0)
        used += seeded_used.get(slot_name, Decimal(0))
        assert agent_row.prereserved == prereserved, f"prereserved mismatch on {slot_name}"
        assert agent_row.reserved == reserved, f"reserved mismatch on {slot_name}"
        assert agent_row.used == used, f"used mismatch on {slot_name}"


async def _kernel_statuses(db: ExtendedAsyncSAEngine, session_id: SessionId) -> set[KernelStatus]:
    async with db.begin_readonly_session() as db_sess:
        rows = (
            await db_sess.execute(
                sa.select(KernelRow.status).where(KernelRow.session_id == session_id)
            )
        ).all()
    return {row.status for row in rows}


class TestPrereservationLifecycle:
    @pytest.fixture
    async def pending_session(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_domain_id: DomainID,
        test_scaling_group_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> tuple[SessionId, list[KernelId], str]:
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            domain_id=test_domain_id,
            scaling_group_name=test_scaling_group_name,
            resource_group_id=test_scaling_group_id,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("2048"))],
            kernel_status=KernelStatus.PENDING,
            assign_agents=False,
        )
        return session_id, kernel_ids, test_agent_id

    async def _reserve(
        self,
        db: ExtendedAsyncSAEngine,
        session_id: SessionId,
        kernel_ids: list[KernelId],
        agent_id: str,
    ) -> list[SessionId]:
        db_source = ScheduleDBSource(db)
        allocations = make_session_allocations(
            session_id=session_id,
            kernel_assignments=[(kernel_id, agent_id) for kernel_id in kernel_ids],
        )
        return await db_source.reserve_sessions(allocations)

    async def test_reserve_holds_prereserved_over_capacity_overlap(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pending_session: tuple[SessionId, list[KernelId], str],
    ) -> None:
        """The victims' ``used`` may overlap the new hold; only
        ``reserved + prereserved <= capacity`` is enforced."""
        session_id, kernel_ids, agent_id = pending_session
        # Agent is fully used by victims: capacity 4/4096, used 4/4096
        await seed_agent_resources(
            db_with_cleanup,
            agent_id,
            cpu_capacity=Decimal("4"),
            mem_capacity=Decimal("4096"),
            cpu_used=Decimal("4"),
            mem_used=Decimal("4096"),
        )

        reserved = await self._reserve(db_with_cleanup, session_id, kernel_ids, agent_id)

        assert reserved == [session_id]
        assert await _kernel_statuses(db_with_cleanup, session_id) == {KernelStatus.RESERVED}
        agent_rows = await fetch_agent_resources(db_with_cleanup, agent_id)
        assert agent_rows["cpu"].prereserved == Decimal("2")
        assert agent_rows["cpu"].used == Decimal("4")
        await _assert_ledger_invariant(
            db_with_cleanup,
            agent_id,
            seeded_used={"cpu": Decimal("4"), "mem": Decimal("4096")},
        )

    async def test_reserve_rejects_unsatisfiable_hold(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pending_session: tuple[SessionId, list[KernelId], str],
    ) -> None:
        """A hold that could never fit the capacity rolls the batch back."""
        session_id, kernel_ids, agent_id = pending_session
        await seed_agent_resources(
            db_with_cleanup,
            agent_id,
            cpu_capacity=Decimal("1"),
            mem_capacity=Decimal("4096"),
        )

        reserved = await self._reserve(db_with_cleanup, session_id, kernel_ids, agent_id)

        assert reserved == []
        assert await _kernel_statuses(db_with_cleanup, session_id) == {KernelStatus.PENDING}
        agent_rows = await fetch_agent_resources(db_with_cleanup, agent_id)
        assert agent_rows["cpu"].prereserved == Decimal("0")

    async def test_admit_waits_until_victims_free_then_moves_hold(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pending_session: tuple[SessionId, list[KernelId], str],
    ) -> None:
        session_id, kernel_ids, agent_id = pending_session
        await seed_agent_resources(
            db_with_cleanup,
            agent_id,
            cpu_capacity=Decimal("4"),
            mem_capacity=Decimal("4096"),
            cpu_used=Decimal("3"),
            mem_used=Decimal("4096"),
        )
        await self._reserve(db_with_cleanup, session_id, kernel_ids, agent_id)
        db_source = ScheduleDBSource(db_with_cleanup)

        # Victims still hold too much: used 3 + hold 2 > capacity 4
        admitted = await db_source.admit_prereserved_kernels([session_id])
        assert admitted == []
        assert await _kernel_statuses(db_with_cleanup, session_id) == {KernelStatus.RESERVED}

        # Victims freed: used drops within capacity
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.text("UPDATE agent_resources SET used = 0 WHERE agent_id = :aid").bindparams(
                    aid=agent_id
                )
            )

        admitted = await db_source.admit_prereserved_kernels([session_id])
        assert admitted == kernel_ids
        assert await _kernel_statuses(db_with_cleanup, session_id) == {KernelStatus.SCHEDULED}
        agent_rows = await fetch_agent_resources(db_with_cleanup, agent_id)
        assert agent_rows["cpu"].prereserved == Decimal("0")
        assert agent_rows["cpu"].reserved == Decimal("2")
        await _assert_ledger_invariant(db_with_cleanup, agent_id)

    async def test_full_lifecycle_ends_at_zero(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pending_session: tuple[SessionId, list[KernelId], str],
    ) -> None:
        """reserve -> admit -> RUNNING -> free returns every counter to zero."""
        session_id, kernel_ids, agent_id = pending_session
        await seed_agent_resources(
            db_with_cleanup,
            agent_id,
            cpu_capacity=Decimal("4"),
            mem_capacity=Decimal("4096"),
        )
        await self._reserve(db_with_cleanup, session_id, kernel_ids, agent_id)
        db_source = ScheduleDBSource(db_with_cleanup)
        admitted = await db_source.admit_prereserved_kernels([session_id])
        assert admitted == kernel_ids

        # RUNNING: the hold moves from reserved into used
        async with db_with_cleanup.begin_session_read_committed() as db_sess:
            for kernel_id in kernel_ids:
                await db_source._allocate_kernel_resources(
                    db_sess,
                    kernel_id,
                    AgentId(agent_id),
                    ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("2048")}),
                )
        agent_rows = await fetch_agent_resources(db_with_cleanup, agent_id)
        assert agent_rows["cpu"].reserved == Decimal("0")
        assert agent_rows["cpu"].used == Decimal("2")
        await _assert_ledger_invariant(db_with_cleanup, agent_id)

        # Free: everything returns to zero
        async with db_with_cleanup.begin_session_read_committed() as db_sess:
            now = await db_source._get_db_now_in_session(db_sess)
            await db_source._free_allocations_and_release(db_sess, list(kernel_ids), now)
        agent_rows = await fetch_agent_resources(db_with_cleanup, agent_id)
        assert agent_rows["cpu"].prereserved == Decimal("0")
        assert agent_rows["cpu"].reserved == Decimal("0")
        assert agent_rows["cpu"].used == Decimal("0")

    async def test_cancel_while_reserved_releases_prereserved(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pending_session: tuple[SessionId, list[KernelId], str],
    ) -> None:
        """A RESERVED session freed before admission releases its
        ``prereserved`` hold exactly."""
        session_id, kernel_ids, agent_id = pending_session
        await seed_agent_resources(
            db_with_cleanup,
            agent_id,
            cpu_capacity=Decimal("4"),
            mem_capacity=Decimal("4096"),
            cpu_used=Decimal("4"),
            mem_used=Decimal("4096"),
        )
        await self._reserve(db_with_cleanup, session_id, kernel_ids, agent_id)
        db_source = ScheduleDBSource(db_with_cleanup)

        async with db_with_cleanup.begin_session_read_committed() as db_sess:
            now = await db_source._get_db_now_in_session(db_sess)
            await db_source._free_allocations_and_release(db_sess, list(kernel_ids), now)

        agent_rows = await fetch_agent_resources(db_with_cleanup, agent_id)
        assert agent_rows["cpu"].prereserved == Decimal("0")
        assert agent_rows["cpu"].used == Decimal("4")
        await _assert_ledger_invariant(
            db_with_cleanup,
            agent_id,
            seeded_used={"cpu": Decimal("4"), "mem": Decimal("4096")},
        )
