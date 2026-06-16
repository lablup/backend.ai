"""
Tests for the BA-6134 ``agent_resources.reserved`` feature.

Group A: SCHEDULED reservation via ``allocate_sessions`` increments
``reserved`` (without overcommit), is idempotent, and rolls back the whole
batch on a capacity gate.

Group C: a SCHEDULED-but-never-RUNNING kernel releases ``reserved`` (not
``used``) on cancel/terminate, and a full lifecycle ends at zero.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import sqlalchemy as sa

from ai.backend.common.types import AccessKey, KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_slot import ResourceAllocationRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource

from .conftest import (
    create_pending_session_with_kernels,
    fetch_agent_resources,
    make_allocation_batch,
    make_creation_info,
    seed_agent_resources,
)


class TestAllocateSessionsReservation:
    """Group A: reservation via allocate_sessions."""

    async def test_a1_single_kernel_reserves_and_schedules(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """A1: reserved += requested, kernel SCHEDULED, session still PENDING, id returned."""
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("10"),
            mem_capacity=Decimal("10240"),
        )
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
        )
        batch = make_allocation_batch(
            session_id=session_id,
            scaling_group_name=test_scaling_group_name,
            access_key=test_access_key,
            kernel_assignments=[(kernel_ids[0], test_agent_id, Decimal("2"), Decimal("4096"))],
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.allocate_sessions(batch)
        assert result == [session_id]

        resources = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert resources["cpu"].reserved == Decimal("2")
        assert resources["mem"].reserved == Decimal("4096")
        assert resources["cpu"].used == Decimal("0")
        assert resources["mem"].used == Decimal("0")

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kernel = (
                await db_sess.execute(sa.select(KernelRow).where(KernelRow.id == kernel_ids[0]))
            ).scalar_one()
            assert kernel.status == KernelStatus.SCHEDULED
            assert kernel.agent == test_agent_id
            assert kernel.agent_addr == "127.0.0.1:6001"

            session = (
                await db_sess.execute(sa.select(SessionRow).where(SessionRow.id == session_id))
            ).scalar_one()
            assert session.status == SessionStatus.PENDING

    async def test_a2_multi_kernel_reserves_sum(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """A2: two kernels on one agent -> reserved is the sum of both requests."""
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("10"),
            mem_capacity=Decimal("10240"),
        )
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_assignments=[
                (test_agent_id, Decimal("2"), Decimal("4096")),
                (test_agent_id, Decimal("3"), Decimal("2048")),
            ],
        )
        batch = make_allocation_batch(
            session_id=session_id,
            scaling_group_name=test_scaling_group_name,
            access_key=test_access_key,
            kernel_assignments=[
                (kernel_ids[0], test_agent_id, Decimal("2"), Decimal("4096")),
                (kernel_ids[1], test_agent_id, Decimal("3"), Decimal("2048")),
            ],
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.allocate_sessions(batch)
        assert result == [session_id]

        resources = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert resources["cpu"].reserved == Decimal("5")  # 2 + 3
        assert resources["mem"].reserved == Decimal("6144")  # 4096 + 2048

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            for kernel_id in kernel_ids:
                kernel = (
                    await db_sess.execute(sa.select(KernelRow).where(KernelRow.id == kernel_id))
                ).scalar_one()
                assert kernel.status == KernelStatus.SCHEDULED

    async def test_a3_idempotent_double_allocate(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """A3: a second allocate of the same batch does not double-increment reserved."""
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("10"),
            mem_capacity=Decimal("10240"),
        )
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
        )
        batch = make_allocation_batch(
            session_id=session_id,
            scaling_group_name=test_scaling_group_name,
            access_key=test_access_key,
            kernel_assignments=[(kernel_ids[0], test_agent_id, Decimal("2"), Decimal("4096"))],
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        first = await db_source.allocate_sessions(batch)
        second = await db_source.allocate_sessions(batch)
        assert first == [session_id]
        assert second == [session_id]

        resources = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert resources["cpu"].reserved == Decimal("2")  # not 4
        assert resources["mem"].reserved == Decimal("4096")  # not 8192

    async def test_a4_capacity_gate_rolls_back(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """A4: a request exceeding reserved+used+req<=capacity returns [] and changes nothing."""
        # capacity cpu=4, already used 3 -> a request of 2 would make 3+0+2 > 4.
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("4"),
            mem_capacity=Decimal("10240"),
            cpu_used=Decimal("3"),
        )
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_assignments=[(test_agent_id, Decimal("2"), Decimal("4096"))],
        )
        batch = make_allocation_batch(
            session_id=session_id,
            scaling_group_name=test_scaling_group_name,
            access_key=test_access_key,
            kernel_assignments=[(kernel_ids[0], test_agent_id, Decimal("2"), Decimal("4096"))],
        )

        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.allocate_sessions(batch)
        assert result == []

        resources = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert resources["cpu"].reserved == Decimal("0")  # unchanged
        assert resources["mem"].reserved == Decimal("0")
        assert resources["cpu"].used == Decimal("3")  # unchanged

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            kernel = (
                await db_sess.execute(sa.select(KernelRow).where(KernelRow.id == kernel_ids[0]))
            ).scalar_one()
            assert kernel.status == KernelStatus.PENDING

    async def test_a5_batch_atomicity_second_session_exceeds(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """A5: two sessions in one batch; second exceeds capacity -> whole batch rolls back."""
        # cpu capacity 5: first session reserves 3, second wants 3 -> 3+3 > 5.
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("5"),
            mem_capacity=Decimal("102400"),
        )
        session_a, kernels_a = await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_assignments=[(test_agent_id, Decimal("3"), Decimal("4096"))],
        )
        session_b, kernels_b = await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_assignments=[(test_agent_id, Decimal("3"), Decimal("4096"))],
        )

        batch_a = make_allocation_batch(
            session_id=session_a,
            scaling_group_name=test_scaling_group_name,
            access_key=test_access_key,
            kernel_assignments=[(kernels_a[0], test_agent_id, Decimal("3"), Decimal("4096"))],
        )
        batch_b = make_allocation_batch(
            session_id=session_b,
            scaling_group_name=test_scaling_group_name,
            access_key=test_access_key,
            kernel_assignments=[(kernels_b[0], test_agent_id, Decimal("3"), Decimal("4096"))],
        )
        # Combine both session allocations into one batch.
        batch_a.allocations.extend(batch_b.allocations)

        db_source = ScheduleDBSource(db_with_cleanup)
        result = await db_source.allocate_sessions(batch_a)
        assert result == []

        resources = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert resources["cpu"].reserved == Decimal("0")
        assert resources["mem"].reserved == Decimal("0")

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            for kernel_id in kernels_a + kernels_b:
                kernel = (
                    await db_sess.execute(sa.select(KernelRow).where(KernelRow.id == kernel_id))
                ).scalar_one()
                assert kernel.status == KernelStatus.PENDING


class TestReservedOnlyRelease:
    """Group C: a SCHEDULED-but-never-RUNNING kernel releases reserved, not used."""

    async def _allocate_one(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        scaling_group_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        agent_id: str,
        cpu: Decimal = Decimal("2"),
        mem: Decimal = Decimal("4096"),
    ) -> tuple[SessionId, KernelId]:
        """Create a PENDING session and allocate it (-> SCHEDULED, reserved up)."""
        session_id, kernel_ids = await create_pending_session_with_kernels(
            db,
            domain_name=domain_name,
            scaling_group_name=scaling_group_name,
            group_id=group_id,
            user_uuid=user_uuid,
            access_key=access_key,
            agent_assignments=[(agent_id, cpu, mem)],
        )
        batch = make_allocation_batch(
            session_id=session_id,
            scaling_group_name=scaling_group_name,
            access_key=access_key,
            kernel_assignments=[(kernel_ids[0], agent_id, cpu, mem)],
        )
        result = await ScheduleDBSource(db).allocate_sessions(batch)
        assert result == [session_id]
        return session_id, kernel_ids[0]

    async def test_c2_cancel_releases_reserved(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """C2: cancelling a SCHEDULED kernel decrements reserved; used unchanged; free_at set."""
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("10"),
            mem_capacity=Decimal("10240"),
        )
        db_source = ScheduleDBSource(db_with_cleanup)
        _, kernel_id = await self._allocate_one(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        before = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert before["cpu"].reserved == Decimal("2")

        cancelled = await db_source.update_kernel_status_cancelled(kernel_id, "test-cancel")
        assert cancelled is True

        after = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert after["cpu"].reserved == Decimal("0")
        assert after["mem"].reserved == Decimal("0")
        assert after["cpu"].used == Decimal("0")
        assert after["mem"].used == Decimal("0")

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            allocs = (
                (
                    await db_sess.execute(
                        sa.select(ResourceAllocationRow).where(
                            ResourceAllocationRow.kernel_id == kernel_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(allocs) == 2
            for alloc in allocs:
                assert alloc.free_at is not None
                assert alloc.used is None

    async def test_c3_bulk_terminate_releases_reserved(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """C3: bulk-terminating a SCHEDULED-only kernel releases reserved; used unchanged."""
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("10"),
            mem_capacity=Decimal("10240"),
        )
        db_source = ScheduleDBSource(db_with_cleanup)
        _, kernel_id = await self._allocate_one(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
        )

        before = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert before["cpu"].reserved == Decimal("2")

        terminated = await db_source.update_kernels_to_terminated([str(kernel_id)], "test-cleanup")
        assert terminated == 1

        after = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert after["cpu"].reserved == Decimal("0")
        assert after["mem"].reserved == Decimal("0")
        assert after["cpu"].used == Decimal("0")
        assert after["mem"].used == Decimal("0")

    async def test_full_lifecycle_reserved_to_used_to_zero(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """PENDING -> allocate (reserved up) -> RUNNING (reserved->used) -> terminated (zero)."""
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("10"),
            mem_capacity=Decimal("10240"),
        )
        db_source = ScheduleDBSource(db_with_cleanup)
        _, kernel_id = await self._allocate_one(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
            cpu=Decimal("2"),
            mem=Decimal("4096"),
        )

        after_reserve = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert after_reserve["cpu"].reserved == Decimal("2")
        assert after_reserve["cpu"].used == Decimal("0")

        # SCHEDULED -> CREATING (RUNNING requires PREPARED/CREATING source status).
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(KernelRow)
                .where(KernelRow.id == kernel_id)
                .values(status=KernelStatus.CREATING)
            )

        running = await db_source.update_kernel_status_running(
            kernel_id, "test-running", make_creation_info(cpu="2", mem="4096")
        )
        assert running is True

        after_running = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert after_running["cpu"].reserved == Decimal("0")  # moved to used
        assert after_running["cpu"].used == Decimal("2")
        assert after_running["mem"].reserved == Decimal("0")
        assert after_running["mem"].used == Decimal("4096")

        terminated = await db_source.update_kernel_status_terminated(kernel_id, "test-terminated")
        assert terminated is True

        after_term = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert after_term["cpu"].reserved == Decimal("0")
        assert after_term["cpu"].used == Decimal("0")
        assert after_term["mem"].reserved == Decimal("0")
        assert after_term["mem"].used == Decimal("0")
