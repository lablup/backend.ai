"""
Concurrency & cleanup invariants for the BA-6134 ``agent_resources.reserved``
feature.

Each ScheduleDBSource method opens its own DB session, so ``asyncio.gather``
produces real row contention. These tests assert deterministic final-state
invariants (no overcommit, no leak, exact consistency) rather than timing.
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

import sqlalchemy as sa

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey, KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_slot import ResourceAllocationRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource

from .conftest import (
    create_pending_session_with_kernels,
    fetch_agent_resources,
    make_allocation_batch,
    make_creation_info,
    seed_agent_resources,
)


async def _set_kernel_status(
    db: ExtendedAsyncSAEngine,
    kernel_id: KernelId,
    status: KernelStatus,
) -> None:
    """Force a kernel into a given status (test plumbing only)."""
    async with db.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(KernelRow).where(KernelRow.id == kernel_id).values(status=status)
        )


class TestReservedConcurrency:
    """Group E: concurrency races and repeated allocate/free leave no overcommit or leak."""

    async def test_e1_concurrent_reservation_no_overcommit(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """E1: N concurrent allocations on a capacity-limited agent never overcommit."""
        # cpu capacity 10. Sessions request 2..4 cpu each; only some fit.
        cpu_capacity = Decimal("10")
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=cpu_capacity,
            mem_capacity=Decimal("1048576"),
        )
        db_source = ScheduleDBSource(db_with_cleanup)

        # Mix of single- and multi-kernel sessions.
        session_specs: list[list[tuple[str, Decimal, Decimal]]] = [
            [(test_agent_id, Decimal("3"), Decimal("4096"))],
            [(test_agent_id, Decimal("4"), Decimal("4096"))],
            [
                (test_agent_id, Decimal("2"), Decimal("2048")),
                (test_agent_id, Decimal("2"), Decimal("2048")),
            ],
            [(test_agent_id, Decimal("3"), Decimal("4096"))],
            [(test_agent_id, Decimal("4"), Decimal("4096"))],
            [(test_agent_id, Decimal("2"), Decimal("2048"))],
        ]

        batches = []
        cpu_by_session: dict[SessionId, Decimal] = {}
        for spec in session_specs:
            session_id, kernel_ids = await create_pending_session_with_kernels(
                db_with_cleanup,
                domain_id=test_domain_id,
                domain_name=test_domain_name,
                resource_group_id=test_scaling_group_id,
                scaling_group_name=test_scaling_group_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
                agent_assignments=spec,
            )
            cpu_by_session[session_id] = sum((cpu for _, cpu, _ in spec), Decimal("0"))
            batches.append(
                make_allocation_batch(
                    session_id=session_id,
                    scaling_group_name=test_scaling_group_name,
                    resource_group_id=test_scaling_group_id,
                    access_key=test_access_key,
                    kernel_assignments=[
                        (kernel_ids[i], agent_id, cpu, mem)
                        for i, (agent_id, cpu, mem) in enumerate(spec)
                    ],
                )
            )

        results = await asyncio.gather(*(db_source.allocate_sessions(b) for b in batches))

        scheduled_session_ids = {sid for r in results for sid in r}
        expected_reserved = sum(
            (cpu_by_session[sid] for sid in scheduled_session_ids), Decimal("0")
        )

        resources = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        # No overcommit.
        assert resources["cpu"].reserved <= cpu_capacity
        # reserved equals the sum over kernels that actually became SCHEDULED.
        assert resources["cpu"].reserved == expected_reserved

        # Losers returned [] and left no residual: every PENDING session has no reserved share.
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            scheduled_kernels = (
                (
                    await db_sess.execute(
                        sa.select(KernelRow.session_id)
                        .where(KernelRow.agent == test_agent_id)
                        .where(KernelRow.status == KernelStatus.SCHEDULED)
                    )
                )
                .scalars()
                .all()
            )
        assert set(scheduled_kernels) == scheduled_session_ids

    async def test_e2_repeated_lifecycle_no_leak(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """E2: many sequential + concurrent allocate->run->terminate cycles leave zero."""
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("4"),
            mem_capacity=Decimal("10240"),
        )
        db_source = ScheduleDBSource(db_with_cleanup)

        async def one_cycle() -> None:
            session_id, kernel_ids = await create_pending_session_with_kernels(
                db_with_cleanup,
                domain_id=test_domain_id,
                domain_name=test_domain_name,
                resource_group_id=test_scaling_group_id,
                scaling_group_name=test_scaling_group_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
                agent_assignments=[(test_agent_id, Decimal("2"), Decimal("2048"))],
            )
            kernel_id = kernel_ids[0]
            batch = make_allocation_batch(
                session_id=session_id,
                scaling_group_name=test_scaling_group_name,
                resource_group_id=test_scaling_group_id,
                access_key=test_access_key,
                kernel_assignments=[(kernel_id, test_agent_id, Decimal("2"), Decimal("2048"))],
            )
            allocated = await db_source.allocate_sessions(batch)
            if not allocated:
                # Lost a capacity race; cancel to release any partial state and stop.
                await db_source.update_kernel_status_cancelled(kernel_id, "lost-race")
                return
            await _set_kernel_status(db_with_cleanup, kernel_id, KernelStatus.CREATING)
            await db_source.update_kernel_status_running(
                kernel_id, "running", make_creation_info(cpu="2", mem="2048")
            )
            await db_source.update_kernel_status_terminated(kernel_id, "terminated")

        # Sequential cycles.
        for _ in range(30):
            await one_cycle()

        # Concurrent batch of cycles (bounded).
        await asyncio.gather(*(one_cycle() for _ in range(8)))

        resources = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert resources["cpu"].reserved == Decimal("0")
        assert resources["cpu"].used == Decimal("0")
        assert resources["mem"].reserved == Decimal("0")
        assert resources["mem"].used == Decimal("0")

    async def test_e3_interleaved_allocate_free_consistency(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain_name: str,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> None:
        """E3: interleaved allocate/free leaves reserved/used matching live allocations."""
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("20"),
            mem_capacity=Decimal("1048576"),
        )
        db_source = ScheduleDBSource(db_with_cleanup)

        async def allocate_session(*, run: bool) -> tuple[SessionId, KernelId]:
            session_id, kernel_ids = await create_pending_session_with_kernels(
                db_with_cleanup,
                domain_id=test_domain_id,
                domain_name=test_domain_name,
                resource_group_id=test_scaling_group_id,
                scaling_group_name=test_scaling_group_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
                agent_assignments=[(test_agent_id, Decimal("2"), Decimal("2048"))],
            )
            kernel_id = kernel_ids[0]
            batch = make_allocation_batch(
                session_id=session_id,
                scaling_group_name=test_scaling_group_name,
                resource_group_id=test_scaling_group_id,
                access_key=test_access_key,
                kernel_assignments=[(kernel_id, test_agent_id, Decimal("2"), Decimal("2048"))],
            )
            await db_source.allocate_sessions(batch)
            if run:
                await _set_kernel_status(db_with_cleanup, kernel_id, KernelStatus.CREATING)
                await db_source.update_kernel_status_running(
                    kernel_id, "running", make_creation_info(cpu="2", mem="2048")
                )
            return session_id, kernel_id

        # Seed an initial pool: half running, half reserved-only.
        running_kernels: list[KernelId] = []
        reserved_kernels: list[KernelId] = []
        for i in range(6):
            _, kernel_id = await allocate_session(run=(i % 2 == 0))
            (running_kernels if i % 2 == 0 else reserved_kernels).append(kernel_id)

        # Interleave: concurrently allocate new sessions while terminating existing ones.
        async def terminate(kernel_id: KernelId) -> None:
            await db_source.update_kernel_status_terminated(kernel_id, "interleaved-terminate")

        tasks: list[asyncio.Future[object]] = []
        tasks.append(asyncio.ensure_future(allocate_session(run=True)))
        tasks.append(asyncio.ensure_future(allocate_session(run=False)))
        tasks.append(asyncio.ensure_future(terminate(running_kernels[0])))
        tasks.append(asyncio.ensure_future(terminate(reserved_kernels[0])))
        tasks.append(asyncio.ensure_future(allocate_session(run=True)))
        tasks.append(asyncio.ensure_future(terminate(running_kernels[1])))
        await asyncio.gather(*tasks)

        # Derive expected reserved/used from live allocations of kernels on this agent.
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            reserved_row = (
                await db_sess.execute(
                    sa.select(sa.func.coalesce(sa.func.sum(ResourceAllocationRow.requested), 0))
                    .select_from(ResourceAllocationRow)
                    .join(KernelRow, KernelRow.id == ResourceAllocationRow.kernel_id)
                    .where(
                        KernelRow.agent == test_agent_id,
                        ResourceAllocationRow.slot_name == "cpu",
                        ResourceAllocationRow.free_at.is_(None),
                        ResourceAllocationRow.used_at.is_(None),
                    )
                )
            ).scalar_one()
            used_row = (
                await db_sess.execute(
                    sa.select(sa.func.coalesce(sa.func.sum(ResourceAllocationRow.used), 0))
                    .select_from(ResourceAllocationRow)
                    .join(KernelRow, KernelRow.id == ResourceAllocationRow.kernel_id)
                    .where(
                        KernelRow.agent == test_agent_id,
                        ResourceAllocationRow.slot_name == "cpu",
                        ResourceAllocationRow.free_at.is_(None),
                        ResourceAllocationRow.used_at.isnot(None),
                    )
                )
            ).scalar_one()
        # coalesce(..., 0) guarantees a non-null aggregate.
        assert reserved_row is not None
        assert used_row is not None
        expected_reserved = Decimal(reserved_row)
        expected_used = Decimal(used_row)

        resources = await fetch_agent_resources(db_with_cleanup, test_agent_id)
        assert resources["cpu"].reserved >= Decimal("0")
        assert resources["cpu"].used >= Decimal("0")
        assert resources["cpu"].reserved == expected_reserved
        assert resources["cpu"].used == expected_used
