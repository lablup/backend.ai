"""Tests for ScheduleDBSource.update_kernel_status_transition (BEP-1061 3e).

Applying an Agent-reported ``from -> to`` kernel transition atomically and
recording it into ``kernel_scheduling_history`` in the same transaction.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from decimal import Decimal

import pytest
from dateutil.tz import tzutc
from sqlalchemy import select

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.scheduling_history.row import KernelSchedulingHistoryRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource


@pytest.fixture
async def pulling_kernel(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain_name: str,
    test_domain_id: DomainID,
    test_scaling_group_name: str,
    test_scaling_group_id: ResourceGroupID,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    test_access_key: AccessKey,
) -> AsyncGenerator[tuple[SessionId, KernelId], None]:
    """A session with one kernel in PULLING status, inserted directly."""
    session_id = SessionId(uuid.uuid4())
    kernel_id = KernelId(uuid.uuid4())
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            SessionRow(
                id=session_id,
                name=f"test-session-{uuid.uuid4().hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                domain_name=test_domain_name,
                domain_id=test_domain_id,
                group_id=test_group_id,
                scaling_group_name=test_scaling_group_name,
                resource_group_id=test_scaling_group_id,
                status=SessionStatus.PREPARING,
                status_info="test",
                cluster_mode=ClusterMode.SINGLE_NODE,
                requested_slots=ResourceSlot({"cpu": Decimal("1")}),
                created_at=datetime.now(tzutc()),
                images=["python:3.13"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
            )
        )
        await db_sess.flush()
        db_sess.add(
            KernelRow(
                id=kernel_id,
                session_id=session_id,
                agent=None,
                agent_addr=None,
                scaling_group=test_scaling_group_name,
                resource_group_id=test_scaling_group_id,
                cluster_idx=0,
                cluster_role="main",
                cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                image="python:3.13",
                architecture="x86_64",
                registry="docker.io",
                container_id=None,
                status=KernelStatus.PULLING,
                status_changed=datetime.now(tzutc()),
                occupied_slots=ResourceSlot(),
                requested_slots=ResourceSlot({"cpu": Decimal("1")}),
                domain_name=test_domain_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
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
        await db_sess.flush()
    yield session_id, kernel_id


async def _kernel_state(
    db: ExtendedAsyncSAEngine, kernel_id: KernelId
) -> tuple[KernelStatus, list[KernelSchedulingHistoryRow]]:
    """Fetch the kernel's current status and its ordered history rows in one session."""
    async with db.begin_readonly_session() as db_sess:
        status = await db_sess.scalar(select(KernelRow.status).where(KernelRow.id == kernel_id))
        result = await db_sess.execute(
            select(KernelSchedulingHistoryRow)
            .where(KernelSchedulingHistoryRow.kernel_id == kernel_id)
            .order_by(KernelSchedulingHistoryRow.created_at)
        )
        return status, list(result.scalars().all())


class TestUpdateKernelStatusTransition:
    async def test_applies_transition_and_records_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pulling_kernel: tuple[SessionId, KernelId],
    ) -> None:
        session_id, kernel_id = pulling_kernel
        db_source = ScheduleDBSource(db_with_cleanup)

        applied = await db_source.update_kernel_status_transition(
            kernel_id,
            KernelStatus.PULLING,
            KernelStatus.PREPARED,
            "image-pulled",
            SchedulingResult.SUCCESS,
            None,
            "prepare done",
        )

        assert applied is True
        status, rows = await _kernel_state(db_with_cleanup, kernel_id)
        assert status == KernelStatus.PREPARED
        assert len(rows) == 1
        assert rows[0].session_id == session_id
        assert rows[0].phase == "prepare"
        assert rows[0].from_status == "PULLING"
        assert rows[0].to_status == "PREPARED"
        assert rows[0].result == str(SchedulingResult.SUCCESS)
        assert rows[0].attempts == 1

    async def test_stale_transition_rejected_without_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pulling_kernel: tuple[SessionId, KernelId],
    ) -> None:
        _, kernel_id = pulling_kernel
        db_source = ScheduleDBSource(db_with_cleanup)

        applied = await db_source.update_kernel_status_transition(
            kernel_id,
            KernelStatus.CREATING,  # does not match the current PULLING status
            KernelStatus.RUNNING,
            "stale",
            SchedulingResult.SUCCESS,
            None,
            "stale transition",
        )

        assert applied is False
        status, rows = await _kernel_state(db_with_cleanup, kernel_id)
        assert status == KernelStatus.PULLING
        assert rows == []

    async def test_redelivered_applied_transition_rejected(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pulling_kernel: tuple[SessionId, KernelId],
    ) -> None:
        _, kernel_id = pulling_kernel
        db_source = ScheduleDBSource(db_with_cleanup)

        first = await db_source.update_kernel_status_transition(
            kernel_id,
            KernelStatus.PULLING,
            KernelStatus.PREPARED,
            "image-pulled",
            SchedulingResult.SUCCESS,
            None,
            "prepare done",
        )
        redelivered = await db_source.update_kernel_status_transition(
            kernel_id,
            KernelStatus.PULLING,
            KernelStatus.PREPARED,
            "image-pulled",
            SchedulingResult.SUCCESS,
            None,
            "prepare done",
        )

        assert first is True
        assert redelivered is False
        _, rows = await _kernel_state(db_with_cleanup, kernel_id)
        assert len(rows) == 1
        assert rows[0].attempts == 1

    async def test_failed_report_records_without_status_change(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pulling_kernel: tuple[SessionId, KernelId],
    ) -> None:
        session_id, kernel_id = pulling_kernel
        db_source = ScheduleDBSource(db_with_cleanup)

        recorded = await db_source.update_kernel_status_transition(
            kernel_id,
            KernelStatus.PULLING,
            KernelStatus.PREPARED,
            "image-pull-failed",
            SchedulingResult.FAILURE,
            "PULL_TIMEOUT",
            "registry timeout",
        )

        assert recorded is True
        status, rows = await _kernel_state(db_with_cleanup, kernel_id)
        assert status == KernelStatus.PULLING
        assert len(rows) == 1
        assert rows[0].session_id == session_id
        assert rows[0].result == str(SchedulingResult.FAILURE)
        assert rows[0].error_code == "PULL_TIMEOUT"

    async def test_repeated_failed_report_merges_attempts(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pulling_kernel: tuple[SessionId, KernelId],
    ) -> None:
        _, kernel_id = pulling_kernel
        db_source = ScheduleDBSource(db_with_cleanup)

        for _ in range(2):
            await db_source.update_kernel_status_transition(
                kernel_id,
                KernelStatus.PULLING,
                KernelStatus.PREPARED,
                "image-pull-failed",
                SchedulingResult.FAILURE,
                "PULL_TIMEOUT",
                "registry timeout",
            )

        _, rows = await _kernel_state(db_with_cleanup, kernel_id)
        assert len(rows) == 1
        assert rows[0].attempts == 2

    async def test_non_reportable_target_status_ignored(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pulling_kernel: tuple[SessionId, KernelId],
    ) -> None:
        _, kernel_id = pulling_kernel
        db_source = ScheduleDBSource(db_with_cleanup)

        applied = await db_source.update_kernel_status_transition(
            kernel_id,
            KernelStatus.PULLING,
            KernelStatus.CANCELLED,  # not an Agent-reportable phase
            "cancelled",
            SchedulingResult.SUCCESS,
            None,
            "cancel is sokovan's concern",
        )

        assert applied is False
        status, rows = await _kernel_state(db_with_cleanup, kernel_id)
        assert status == KernelStatus.PULLING
        assert rows == []
