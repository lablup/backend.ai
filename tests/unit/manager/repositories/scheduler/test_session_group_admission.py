"""All-or-none admission in the scheduler repository against a real database (BEP-1083)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TypedDict

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.session_group import (
    SessionGroupFull,
    SessionGroupResourceGroupMismatch,
)
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.views.sokovan.workload import GroupAdmission
from ai.backend.sokovan_core.types.policy import (
    SessionGroupAdmission,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import create_pending_session_with_kernels


class SessionScope(TypedDict):
    domain_id: DomainID
    domain_name: str
    resource_group_id: ResourceGroupID
    resource_group_name: str
    group_id: uuid.UUID
    user_uuid: uuid.UUID
    access_key: AccessKey


@pytest.fixture
def db_source(db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
    return ScheduleDBSource(
        db_with_cleanup,
        ReconcileOpsProvider(db_with_cleanup),
        KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )


@pytest.fixture
def session_scope(
    test_domain_id: DomainID,
    test_domain: DomainFixtureData,
    test_scaling_group_id: ResourceGroupID,
    test_scaling_group_name: str,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    test_access_key: AccessKey,
) -> SessionScope:
    return {
        "domain_id": test_domain_id,
        "domain_name": test_domain.domain_name,
        "resource_group_id": test_scaling_group_id,
        "resource_group_name": test_scaling_group_name,
        "group_id": test_group_id,
        "user_uuid": test_user_uuid,
        "access_key": test_access_key,
    }


async def _create_group(
    db: ExtendedAsyncSAEngine,
    scope: SessionScope,
    admission: SessionGroupAdmission,
    member_count: int | None,
) -> SessionGroupID:
    group_id = SessionGroupID(uuid.uuid4())
    async with db.begin_session() as db_sess:
        db_sess.add(
            SessionGroupRow(
                id=group_id,
                domain_id=scope["domain_id"],
                project_id=ProjectID(scope["group_id"]),
                owner_user_id=UserID(scope["user_uuid"]),
                placement_direction=SessionGroupPlacementDirection.SPREAD,
                placement_enforcement=SessionGroupPlacementEnforcement.STRICT,
                admission=admission,
                member_count=member_count,
            )
        )
    return group_id


async def _add_member(
    db: ExtendedAsyncSAEngine,
    scope: SessionScope,
    agent_id: str,
    group_id: SessionGroupID,
    status: SessionStatus = SessionStatus.PENDING,
) -> SessionId:
    session_id, _ = await create_pending_session_with_kernels(
        db,
        agent_assignments=[(agent_id, Decimal("1"), Decimal("1024"))],
        session_status=status,
        kernel_status=KernelStatus.PENDING
        if status == SessionStatus.PENDING
        else KernelStatus.CREATING,
        session_group_id=group_id,
        **scope,
    )
    return session_id


async def _read(db: ExtendedAsyncSAEngine, session_id: SessionId) -> SessionRow:
    async with db.begin_readonly_session() as db_sess:
        row = await db_sess.scalar(sa.select(SessionRow).where(SessionRow.id == session_id))
        assert row is not None
        return row


@pytest.fixture
async def all_or_none_group(
    db_with_cleanup: ExtendedAsyncSAEngine, session_scope: SessionScope
) -> SessionGroupID:
    return await _create_group(db_with_cleanup, session_scope, SessionGroupAdmission.ALL_OR_NONE, 2)


@pytest.fixture
async def independent_group(
    db_with_cleanup: ExtendedAsyncSAEngine, session_scope: SessionScope
) -> SessionGroupID:
    return await _create_group(
        db_with_cleanup, session_scope, SessionGroupAdmission.INDEPENDENT, None
    )


@pytest.fixture
async def kubernetes_resource_group(
    db_with_cleanup: ExtendedAsyncSAEngine, test_scaling_group_name: str
) -> str:
    async with db_with_cleanup.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(ResourceGroupRow)
            .where(ResourceGroupRow.name == test_scaling_group_name)
            .values(driver="kubernetes", driver_opts={"compute_cluster": "k8s-a"})
        )
    return test_scaling_group_name


class TestPendingWorkloadAdmission:
    async def test_an_all_or_none_member_carries_the_admission(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        all_or_none_group: SessionGroupID,
    ) -> None:
        await _add_member(db_with_cleanup, session_scope, test_agent_id, all_or_none_group)

        fetch = await db_source.fetch_scheduling_fetch(session_scope["resource_group_id"])

        assert fetch is not None
        [workload] = fetch.workloads
        assert workload.group_admission == GroupAdmission(
            group_id=all_or_none_group, member_count=2
        )
        assert workload.placement.session_group is not None

    async def test_an_independent_member_has_no_admission(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        independent_group: SessionGroupID,
    ) -> None:
        await _add_member(db_with_cleanup, session_scope, test_agent_id, independent_group)

        fetch = await db_source.fetch_scheduling_fetch(session_scope["resource_group_id"])

        assert fetch is not None
        assert fetch.workloads[0].group_admission is None

    async def test_a_kubernetes_group_leaves_the_placement_policy_to_the_cluster(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        kubernetes_resource_group: str,
        all_or_none_group: SessionGroupID,
    ) -> None:
        await _add_member(db_with_cleanup, session_scope, test_agent_id, all_or_none_group)

        fetch = await db_source.fetch_scheduling_fetch(session_scope["resource_group_id"])

        assert fetch is not None
        [workload] = fetch.workloads
        assert workload.placement.session_group is None
        assert workload.group_admission is not None
        assert fetch.session_group_members == {}


class TestPendingStatusInfo:
    async def test_only_pending_sessions_get_the_reason(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        all_or_none_group: SessionGroupID,
    ) -> None:
        pending = await _add_member(
            db_with_cleanup, session_scope, test_agent_id, all_or_none_group
        )
        creating = await _add_member(
            db_with_cleanup,
            session_scope,
            test_agent_id,
            all_or_none_group,
            SessionStatus.CREATING,
        )

        await db_source.mark_pending_sessions_status_info(
            [pending, creating], "waiting-for-group-members"
        )

        assert (await _read(db_with_cleanup, pending)).status_info == "waiting-for-group-members"
        assert (await _read(db_with_cleanup, creating)).status_info != "waiting-for-group-members"


class TestAdmitSessionGroupMember:
    async def _admit(
        self,
        db: ExtendedAsyncSAEngine,
        group_id: SessionGroupID,
        resource_group_id: ResourceGroupID,
    ) -> None:
        async with ReconcileOpsProvider(db).write_ops() as w:
            await w.admit_session_group_member(group_id, resource_group_id)

    async def test_a_member_below_the_count_joins(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        all_or_none_group: SessionGroupID,
    ) -> None:
        await _add_member(db_with_cleanup, session_scope, test_agent_id, all_or_none_group)

        await self._admit(db_with_cleanup, all_or_none_group, session_scope["resource_group_id"])

    async def test_a_member_beyond_the_count_is_rejected(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        all_or_none_group: SessionGroupID,
    ) -> None:
        for _ in range(2):
            await _add_member(db_with_cleanup, session_scope, test_agent_id, all_or_none_group)

        with pytest.raises(SessionGroupFull):
            await self._admit(
                db_with_cleanup, all_or_none_group, session_scope["resource_group_id"]
            )

    async def test_a_member_in_another_resource_group_is_rejected(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        all_or_none_group: SessionGroupID,
    ) -> None:
        await _add_member(db_with_cleanup, session_scope, test_agent_id, all_or_none_group)

        with pytest.raises(SessionGroupResourceGroupMismatch):
            await self._admit(db_with_cleanup, all_or_none_group, ResourceGroupID(uuid.uuid4()))

    async def test_an_independent_group_takes_any_member(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        independent_group: SessionGroupID,
    ) -> None:
        for _ in range(3):
            await _add_member(db_with_cleanup, session_scope, test_agent_id, independent_group)

        await self._admit(db_with_cleanup, independent_group, ResourceGroupID(uuid.uuid4()))


class TestGroupPlacementTimeout:
    async def test_every_admitted_member_is_rescheduled_under_one_count(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        kubernetes_resource_group: str,
        all_or_none_group: SessionGroupID,
    ) -> None:
        timed_out = await _add_member(
            db_with_cleanup, session_scope, test_agent_id, all_or_none_group, SessionStatus.CREATING
        )
        other = await _add_member(
            db_with_cleanup, session_scope, test_agent_id, all_or_none_group, SessionStatus.CREATING
        )
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(SessionRow)
                .where(SessionRow.id == other)
                .values(status_data={"placement_timeout": {"attempts": 2}})
            )

        record = await db_source.record_placement_timeout(timed_out, "unschedulable", None)

        assert record is not None
        assert record.attempts == 3
        assert record.group_member_ids == (other,)
        for session_id in (timed_out, other):
            row = await _read(db_with_cleanup, session_id)
            assert row.status == SessionStatus.RESCHEDULING
            assert row.status_info == "placement-timeout"
            assert row.status_data is not None
            assert row.status_data["placement_timeout"]["attempts"] == 3

    async def test_an_independent_member_is_rescheduled_alone(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_agent_id: str,
        resource_slot_types: None,
        session_scope: SessionScope,
        kubernetes_resource_group: str,
        independent_group: SessionGroupID,
    ) -> None:
        timed_out = await _add_member(
            db_with_cleanup, session_scope, test_agent_id, independent_group, SessionStatus.CREATING
        )
        other = await _add_member(
            db_with_cleanup, session_scope, test_agent_id, independent_group, SessionStatus.CREATING
        )

        record = await db_source.record_placement_timeout(timed_out, "unschedulable", None)

        assert record is not None
        assert record.group_member_ids == ()
        assert (await _read(db_with_cleanup, other)).status == SessionStatus.CREATING
