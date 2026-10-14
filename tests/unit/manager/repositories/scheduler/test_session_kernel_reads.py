"""
Tests for the ScheduleDBSource reads that pair sessions with their kernels.

``get_terminating_sessions_by_ids`` and ``fetch_sessions_for_handler`` read the kernels of
the selected sessions in a separate query keyed by ``KernelRow.session_id``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey, AgentId, KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import create_pending_session_with_kernels


@dataclass(frozen=True)
class _SessionScope:
    """The rows every test session hangs off."""

    domain_id: DomainID
    domain_name: str
    resource_group_id: ResourceGroupID
    resource_group_name: str
    group_id: uuid.UUID
    user_uuid: uuid.UUID
    access_key: AccessKey
    agent_id: str


@dataclass(frozen=True)
class _CreatedSession:
    session_id: SessionId
    kernel_ids: list[KernelId]


async def _create_session(
    db: ExtendedAsyncSAEngine,
    scope: _SessionScope,
    *,
    kernel_count: int,
    session_status: SessionStatus = SessionStatus.RUNNING,
    kernel_status: KernelStatus = KernelStatus.RUNNING,
) -> _CreatedSession:
    session_id, kernel_ids = await create_pending_session_with_kernels(
        db,
        domain_id=scope.domain_id,
        domain_name=scope.domain_name,
        resource_group_id=scope.resource_group_id,
        resource_group_name=scope.resource_group_name,
        group_id=scope.group_id,
        user_uuid=scope.user_uuid,
        access_key=scope.access_key,
        agent_assignments=[(scope.agent_id, Decimal("1"), Decimal("1024"))] * kernel_count,
        session_status=session_status,
        kernel_status=kernel_status,
        assign_agents=True,
    )
    async with db.begin_session() as db_sess:
        for kernel_id in kernel_ids:
            await db_sess.execute(
                sa.update(KernelRow)
                .where(KernelRow.id == kernel_id)
                .values(container_id=f"container-{kernel_id}")
            )
    return _CreatedSession(session_id=session_id, kernel_ids=kernel_ids)


async def _set_kernel_status(
    db: ExtendedAsyncSAEngine, kernel_id: KernelId, status: KernelStatus
) -> None:
    async with db.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(KernelRow).where(KernelRow.id == kernel_id).values(status=status)
        )


@pytest.fixture
def scope(
    test_domain_id: DomainID,
    test_domain: DomainFixtureData,
    test_scaling_group_id: ResourceGroupID,
    test_scaling_group_name: str,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    test_access_key: AccessKey,
    test_agent_id: str,
    resource_slot_types: None,
) -> _SessionScope:
    return _SessionScope(
        domain_id=test_domain_id,
        domain_name=test_domain.domain_name,
        resource_group_id=test_scaling_group_id,
        resource_group_name=test_scaling_group_name,
        group_id=test_group_id,
        user_uuid=test_user_uuid,
        access_key=test_access_key,
        agent_id=test_agent_id,
    )


@pytest.fixture
def db_source(db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
    return ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))


@pytest.fixture
async def two_kernel_session(
    db_with_cleanup: ExtendedAsyncSAEngine, scope: _SessionScope
) -> _CreatedSession:
    return await _create_session(db_with_cleanup, scope, kernel_count=2)


@pytest.fixture
async def one_kernel_session(
    db_with_cleanup: ExtendedAsyncSAEngine, scope: _SessionScope
) -> _CreatedSession:
    return await _create_session(db_with_cleanup, scope, kernel_count=1)


@pytest.fixture
async def kernelless_session(
    db_with_cleanup: ExtendedAsyncSAEngine, scope: _SessionScope
) -> _CreatedSession:
    return await _create_session(db_with_cleanup, scope, kernel_count=0)


class TestGetTerminatingSessionsByIds:
    async def test_each_session_carries_only_its_kernels(
        self,
        db_source: ScheduleDBSource,
        scope: _SessionScope,
        two_kernel_session: _CreatedSession,
        one_kernel_session: _CreatedSession,
    ) -> None:
        result = await db_source.get_terminating_sessions_by_ids([
            two_kernel_session.session_id,
            one_kernel_session.session_id,
        ])

        by_session = {data.session_id: data for data in result}
        assert set(by_session) == {two_kernel_session.session_id, one_kernel_session.session_id}
        for created in (two_kernel_session, one_kernel_session):
            kernels = by_session[created.session_id].kernels
            assert {kernel.kernel_id for kernel in kernels} == set(created.kernel_ids)
            for kernel in kernels:
                assert kernel.status == KernelStatus.RUNNING
                assert kernel.container_id == f"container-{kernel.kernel_id}"
                assert kernel.agent_id == AgentId(scope.agent_id)
                assert kernel.agent_addr == "127.0.0.1:6001"
                assert kernel.occupied_slots["cpu"] == Decimal("1")

    async def test_session_without_kernels_has_no_kernels(
        self,
        db_source: ScheduleDBSource,
        kernelless_session: _CreatedSession,
    ) -> None:
        result = await db_source.get_terminating_sessions_by_ids([kernelless_session.session_id])

        assert [data.session_id for data in result] == [kernelless_session.session_id]
        assert result[0].kernels == []

    async def test_unrequested_sessions_are_left_out(
        self,
        db_source: ScheduleDBSource,
        two_kernel_session: _CreatedSession,
        one_kernel_session: _CreatedSession,
    ) -> None:
        result = await db_source.get_terminating_sessions_by_ids([one_kernel_session.session_id])

        assert [data.session_id for data in result] == [one_kernel_session.session_id]
        assert [kernel.kernel_id for kernel in result[0].kernels] == one_kernel_session.kernel_ids

    async def test_empty_input_returns_empty(self, db_source: ScheduleDBSource) -> None:
        assert await db_source.get_terminating_sessions_by_ids([]) == []


class TestFetchSessionsForHandler:
    async def test_each_session_carries_only_its_kernels(
        self,
        db_source: ScheduleDBSource,
        scope: _SessionScope,
        two_kernel_session: _CreatedSession,
        one_kernel_session: _CreatedSession,
    ) -> None:
        result = await db_source.fetch_sessions_for_handler(
            scope.resource_group_id, [SessionStatus.RUNNING], None
        )

        by_session = {item.session_info.identity.id: item for item in result}
        assert set(by_session) == {two_kernel_session.session_id, one_kernel_session.session_id}
        for created in (two_kernel_session, one_kernel_session):
            kernel_infos = by_session[created.session_id].kernel_infos
            assert {info.id for info in kernel_infos} == set(created.kernel_ids)

    async def test_session_without_kernels_has_no_kernels(
        self,
        db_source: ScheduleDBSource,
        scope: _SessionScope,
        kernelless_session: _CreatedSession,
    ) -> None:
        result = await db_source.fetch_sessions_for_handler(
            scope.resource_group_id, [SessionStatus.RUNNING], None
        )

        assert [item.session_info.identity.id for item in result] == [kernelless_session.session_id]
        assert result[0].kernel_infos == []

    async def test_kernel_status_filter_keeps_sessions_with_a_matching_kernel(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        scope: _SessionScope,
        two_kernel_session: _CreatedSession,
        one_kernel_session: _CreatedSession,
    ) -> None:
        await _set_kernel_status(
            db_with_cleanup, two_kernel_session.kernel_ids[1], KernelStatus.TERMINATED
        )

        result = await db_source.fetch_sessions_for_handler(
            scope.resource_group_id, [SessionStatus.RUNNING], [KernelStatus.TERMINATED]
        )

        assert [item.session_info.identity.id for item in result] == [two_kernel_session.session_id]
        assert {info.id for info in result[0].kernel_infos} == set(two_kernel_session.kernel_ids)

    async def test_session_status_filter_leaves_other_statuses_out(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        db_source: ScheduleDBSource,
        scope: _SessionScope,
        one_kernel_session: _CreatedSession,
    ) -> None:
        terminating = await _create_session(
            db_with_cleanup,
            scope,
            kernel_count=1,
            session_status=SessionStatus.TERMINATING,
            kernel_status=KernelStatus.TERMINATING,
        )

        result = await db_source.fetch_sessions_for_handler(
            scope.resource_group_id, [SessionStatus.TERMINATING], None
        )

        assert [item.session_info.identity.id for item in result] == [terminating.session_id]
        assert [info.id for info in result[0].kernel_infos] == terminating.kernel_ids
