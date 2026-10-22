"""Tests for the START claim of ``ScheduleDBSource``.

A START pass claims a PREPARED session by moving it and its PREPARED kernels to
CREATING before it asks the agents to create them, so that a second pass racing for
the same session finds nothing left to claim and does not launch it again. A pass that
fails before the launch returns the claim.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import cast

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import AccessKey, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import create_pending_session_with_kernels

_CLAIM_REASON = KernelLifecycleEventReason.TRIGGERED_BY_SCHEDULER


async def _session_status(db: ExtendedAsyncSAEngine, session_id: SessionId) -> SessionStatus:
    async with db.begin_readonly_session() as db_sess:
        status = await db_sess.scalar(
            sa.select(SessionRow.status).where(SessionRow.id == session_id)
        )
    return cast(SessionStatus, status)


async def _kernel_statuses(db: ExtendedAsyncSAEngine, session_id: SessionId) -> list[KernelStatus]:
    async with db.begin_readonly_session() as db_sess:
        statuses = await db_sess.scalars(
            sa.select(KernelRow.status).where(KernelRow.session_id == session_id)
        )
    return list(statuses)


class TestClaimSessionsForStart:
    """Only one claim wins a PREPARED session, together with all of its kernels."""

    @pytest.fixture
    def db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        return ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

    @pytest.fixture
    def create_session(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain: DomainFixtureData,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> Callable[..., Awaitable[SessionId]]:
        """Factory for a session with ``kernel_count`` kernels on the test agent."""

        async def _create(
            session_status: SessionStatus = SessionStatus.PREPARED,
            kernel_count: int = 1,
        ) -> SessionId:
            session_id, _ = await create_pending_session_with_kernels(
                db_with_cleanup,
                domain_id=test_domain_id,
                domain_name=test_domain.domain_name,
                resource_group_id=test_scaling_group_id,
                resource_group_name=test_scaling_group_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=test_access_key,
                agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))] * kernel_count,
                session_status=session_status,
                kernel_status=KernelStatus.PREPARED,
                assign_agents=True,
            )
            return session_id

        return _create

    async def test_concurrent_claims_win_a_cluster_session_once(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        create_session: Callable[..., Awaitable[SessionId]],
    ) -> None:
        """Two passes racing for one multi-kernel session: one claims every kernel, the other none."""
        session_id = await create_session(kernel_count=3)

        first, second = await asyncio.gather(
            db_source.claim_sessions_for_start([session_id], _CLAIM_REASON),
            db_source.claim_sessions_for_start([session_id], _CLAIM_REASON),
        )

        assert sorted([first, second], key=len) == [set(), {session_id}]
        assert await _session_status(db_with_cleanup, session_id) == SessionStatus.CREATING
        assert await _kernel_statuses(db_with_cleanup, session_id) == [KernelStatus.CREATING] * 3

    async def test_claim_waits_for_a_pass_holding_the_session(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        create_session: Callable[..., Awaitable[SessionId]],
    ) -> None:
        """A claim queued behind another pass's claim of the session does not take its kernels."""
        session_id = await create_session(kernel_count=2)

        async with db_with_cleanup.begin_session_read_committed() as other_pass:
            await other_pass.execute(
                sa.select(SessionRow.id).where(SessionRow.id == session_id).with_for_update()
            )
            claim = asyncio.create_task(
                db_source.claim_sessions_for_start([session_id], _CLAIM_REASON)
            )
            await asyncio.sleep(0.5)
            assert not claim.done()
            # The other pass claims the session but has not moved the kernels yet.
            await other_pass.execute(
                sa.update(SessionRow)
                .where(SessionRow.id == session_id)
                .values(status=SessionStatus.CREATING)
            )

        assert await claim == set()
        assert await _kernel_statuses(db_with_cleanup, session_id) == [KernelStatus.PREPARED] * 2

    async def test_claimed_session_is_not_claimed_again(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        create_session: Callable[..., Awaitable[SessionId]],
    ) -> None:
        """A later pass gets only the sessions nobody claimed yet."""
        claimed_id = await create_session()
        fresh_id = await create_session()

        assert await db_source.claim_sessions_for_start([claimed_id], _CLAIM_REASON) == {claimed_id}
        assert await db_source.claim_sessions_for_start([claimed_id, fresh_id], _CLAIM_REASON) == {
            fresh_id
        }

    @pytest.mark.parametrize(
        "session_status",
        [SessionStatus.CREATING, SessionStatus.TERMINATING],
    )
    async def test_session_no_longer_prepared_is_not_claimed(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        create_session: Callable[..., Awaitable[SessionId]],
        session_status: SessionStatus,
    ) -> None:
        """A session that left PREPARED keeps its status and its kernels as they are."""
        session_id = await create_session(session_status=session_status)

        assert await db_source.claim_sessions_for_start([session_id], _CLAIM_REASON) == set()
        assert await _session_status(db_with_cleanup, session_id) == session_status
        assert await _kernel_statuses(db_with_cleanup, session_id) == [KernelStatus.PREPARED]

    async def test_release_returns_the_kernels_to_prepared(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        create_session: Callable[..., Awaitable[SessionId]],
    ) -> None:
        """A released session can be claimed and started by the next pass."""
        session_id = await create_session(kernel_count=2)
        await db_source.claim_sessions_for_start([session_id], _CLAIM_REASON)

        released = await db_source.release_sessions_for_start([session_id])

        assert released == 1
        assert await _session_status(db_with_cleanup, session_id) == SessionStatus.PREPARED
        assert await _kernel_statuses(db_with_cleanup, session_id) == [KernelStatus.PREPARED] * 2
        assert await db_source.claim_sessions_for_start([session_id], _CLAIM_REASON) == {session_id}

    async def test_release_leaves_a_session_that_moved_on(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        create_session: Callable[..., Awaitable[SessionId]],
    ) -> None:
        """A claimed session terminated in the meantime is not handed back to START."""
        session_id = await create_session()
        await db_source.claim_sessions_for_start([session_id], _CLAIM_REASON)
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(SessionRow)
                .where(SessionRow.id == session_id)
                .values(status=SessionStatus.TERMINATING)
            )

        assert await db_source.release_sessions_for_start([session_id]) == 0
        assert await _session_status(db_with_cleanup, session_id) == SessionStatus.TERMINATING
        assert await _kernel_statuses(db_with_cleanup, session_id) == [KernelStatus.CREATING]
