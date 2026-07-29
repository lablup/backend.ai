"""
Tests for the terminal-status guard on the TERMINATED transitions of
``ScheduleDBSource``.

A duplicate or late termination event (e.g. the agent's container lifecycle
sync re-reporting an already destroyed container) must not overwrite the
reason and timestamps a kernel already recorded, and must not drag a
CANCELLED / ERROR kernel into TERMINATED.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.types import AccessKey, KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource

from .conftest import create_pending_session_with_kernels, seed_agent_resources

_IDLE_REASON = "idle-utilization"
_LATE_REASON = "self-terminated"


async def _set_kernel_status(
    db: ExtendedAsyncSAEngine,
    kernel_id: KernelId,
    status: KernelStatus,
    status_info: str,
) -> None:
    async with db.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(KernelRow)
            .where(KernelRow.id == kernel_id)
            .values(status=status, status_info=status_info)
        )


async def _fetch_kernel(db: ExtendedAsyncSAEngine, kernel_id: KernelId) -> KernelRow:
    async with db.begin_readonly_session() as db_sess:
        return (
            await db_sess.execute(sa.select(KernelRow).where(KernelRow.id == kernel_id))
        ).scalar_one()


class TestTerminatedStatusGuard:
    """The TERMINATED transitions only accept force-terminatable statuses."""

    @pytest.fixture
    async def seeded_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> str:
        await seed_agent_resources(
            db_with_cleanup,
            test_agent_id,
            cpu_capacity=Decimal("10"),
            mem_capacity=Decimal("10240"),
        )
        return test_agent_id

    @pytest.fixture
    def db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        return ScheduleDBSource(db_with_cleanup)

    async def _create_kernels(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        scaling_group_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        agent_id: str,
        kernel_status: KernelStatus,
        count: int = 1,
    ) -> tuple[SessionId, list[KernelId]]:
        return await create_pending_session_with_kernels(
            db,
            domain_name=domain_name,
            scaling_group_name=scaling_group_name,
            group_id=group_id,
            user_uuid=user_uuid,
            access_key=access_key,
            agent_assignments=[(agent_id, Decimal("2"), Decimal("2048"))] * count,
            session_status=SessionStatus.RUNNING,
            kernel_status=kernel_status,
            assign_agents=kernel_status is not KernelStatus.PENDING,
        )

    async def test_late_event_does_not_overwrite_terminated_kernel(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        seeded_agent_id: str,
    ) -> None:
        """A second termination event keeps the reason and timestamps of the first."""
        _, kernel_ids = await self._create_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=seeded_agent_id,
            kernel_status=KernelStatus.RUNNING,
        )
        kernel_id = kernel_ids[0]

        assert await db_source.update_kernel_status_terminated(kernel_id, _IDLE_REASON) is True
        first = await _fetch_kernel(db_with_cleanup, kernel_id)
        first_terminated_at = first.terminated_at
        first_status_changed = first.status_changed
        first_history = first.status_history
        assert first_history is not None

        assert await db_source.update_kernel_status_terminated(kernel_id, _LATE_REASON) is False

        second = await _fetch_kernel(db_with_cleanup, kernel_id)
        assert second.status == KernelStatus.TERMINATED
        assert second.status_info == _IDLE_REASON
        assert second.terminated_at == first_terminated_at
        assert second.status_changed == first_status_changed
        assert second.status_history == first_history

    @pytest.mark.parametrize(
        "blocked_status",
        [KernelStatus.CANCELLED, KernelStatus.ERROR, KernelStatus.PENDING],
    )
    async def test_late_event_does_not_terminate_blocked_status(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        seeded_agent_id: str,
        blocked_status: KernelStatus,
    ) -> None:
        """CANCELLED / ERROR / PENDING kernels are never moved to TERMINATED."""
        _, kernel_ids = await self._create_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=seeded_agent_id,
            kernel_status=blocked_status,
        )
        kernel_id = kernel_ids[0]

        assert await db_source.update_kernel_status_terminated(kernel_id, _LATE_REASON) is False

        kernel = await _fetch_kernel(db_with_cleanup, kernel_id)
        assert kernel.status == blocked_status
        assert kernel.status_info != _LATE_REASON
        assert kernel.terminated_at is None

    @pytest.mark.parametrize(
        "live_status",
        [KernelStatus.RUNNING, KernelStatus.TERMINATING],
    )
    async def test_live_kernel_still_terminates(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        seeded_agent_id: str,
        live_status: KernelStatus,
    ) -> None:
        """The normal RUNNING / TERMINATING -> TERMINATED transition still succeeds."""
        _, kernel_ids = await self._create_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=seeded_agent_id,
            kernel_status=live_status,
        )
        kernel_id = kernel_ids[0]

        assert await db_source.update_kernel_status_terminated(kernel_id, _IDLE_REASON) is True

        kernel = await _fetch_kernel(db_with_cleanup, kernel_id)
        assert kernel.status == KernelStatus.TERMINATED
        assert kernel.status_info == _IDLE_REASON
        assert kernel.terminated_at is not None

    async def test_bulk_terminate_skips_terminal_kernels(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        seeded_agent_id: str,
    ) -> None:
        """The bulk update carries the same guard: only the live kernel is updated."""
        _, kernel_ids = await self._create_kernels(
            db_with_cleanup,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=seeded_agent_id,
            kernel_status=KernelStatus.RUNNING,
            count=3,
        )
        running_id, terminated_id, cancelled_id = kernel_ids
        await _set_kernel_status(
            db_with_cleanup, terminated_id, KernelStatus.TERMINATED, _IDLE_REASON
        )
        await _set_kernel_status(
            db_with_cleanup, cancelled_id, KernelStatus.CANCELLED, "pending-timeout"
        )

        updated = await db_source.update_kernels_to_terminated(
            [str(kid) for kid in kernel_ids], _LATE_REASON
        )
        assert updated == 1

        running = await _fetch_kernel(db_with_cleanup, running_id)
        assert running.status == KernelStatus.TERMINATED
        assert running.status_info == _LATE_REASON

        terminated = await _fetch_kernel(db_with_cleanup, terminated_id)
        assert terminated.status == KernelStatus.TERMINATED
        assert terminated.status_info == _IDLE_REASON
        assert terminated.terminated_at is None

        cancelled = await _fetch_kernel(db_with_cleanup, cancelled_id)
        assert cancelled.status == KernelStatus.CANCELLED
        assert cancelled.status_info == "pending-timeout"
