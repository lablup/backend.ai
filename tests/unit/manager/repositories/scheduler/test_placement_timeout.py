"""The placement timeout of a session in a compute cluster against a real database."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import ClusterMode, SessionId, SessionResult, SessionTypes
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.testutils.fixtures import DomainFixtureData


@pytest.fixture
def db_source(db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
    return ScheduleDBSource(
        db_with_cleanup,
        ReconcileOpsProvider(db_with_cleanup),
        KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )


@pytest.fixture
async def kubernetes_group(
    db_with_cleanup: ExtendedAsyncSAEngine, test_scaling_group_name: str
) -> str:
    async with db_with_cleanup.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(ResourceGroupRow)
            .where(ResourceGroupRow.name == test_scaling_group_name)
            .values(driver="kubernetes", driver_opts={"compute_cluster": "k8s-a"})
        )
    return test_scaling_group_name


async def _add_session(
    db: ExtendedAsyncSAEngine,
    status: SessionStatus,
    resource_group: str,
    resource_group_id: ResourceGroupID,
    domain: DomainFixtureData,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
) -> SessionId:
    session_id = SessionId(uuid.uuid4())
    async with db.begin_session() as db_sess:
        db_sess.add(
            SessionRow(
                id=session_id,
                name=f"s-{uuid.uuid4().hex[:8]}",
                session_type=SessionTypes.INTERACTIVE,
                domain_id=domain.domain_id,
                domain_name=domain.domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                resource_group_id=resource_group_id,
                scaling_group_name=resource_group,
                status=status,
                cluster_mode=ClusterMode.SINGLE_NODE,
                created_at=datetime.now(tzutc()),
                images=["python:3.8"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
            )
        )
    return session_id


async def _set_status(
    db: ExtendedAsyncSAEngine, session_id: SessionId, status: SessionStatus
) -> None:
    async with db.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(SessionRow).where(SessionRow.id == session_id).values(status=status)
        )


async def _read(db: ExtendedAsyncSAEngine, session_id: SessionId) -> SessionRow:
    async with db.begin_readonly_session() as db_sess:
        row = await db_sess.scalar(sa.select(SessionRow).where(SessionRow.id == session_id))
        assert row is not None
        return row


@pytest.fixture
async def creating_kubernetes_session(
    db_with_cleanup: ExtendedAsyncSAEngine,
    kubernetes_group: str,
    test_scaling_group_id: ResourceGroupID,
    test_domain: DomainFixtureData,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
) -> SessionId:
    return await _add_session(
        db_with_cleanup,
        SessionStatus.CREATING,
        kubernetes_group,
        test_scaling_group_id,
        test_domain,
        test_group_id,
        test_user_uuid,
    )


@pytest.fixture
async def running_kubernetes_session(
    db_with_cleanup: ExtendedAsyncSAEngine,
    kubernetes_group: str,
    test_scaling_group_id: ResourceGroupID,
    test_domain: DomainFixtureData,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
) -> SessionId:
    return await _add_session(
        db_with_cleanup,
        SessionStatus.RUNNING,
        kubernetes_group,
        test_scaling_group_id,
        test_domain,
        test_group_id,
        test_user_uuid,
    )


@pytest.fixture
async def creating_docker_session(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_scaling_group_name: str,
    test_scaling_group_id: ResourceGroupID,
    test_domain: DomainFixtureData,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
) -> SessionId:
    return await _add_session(
        db_with_cleanup,
        SessionStatus.CREATING,
        test_scaling_group_name,
        test_scaling_group_id,
        test_domain,
        test_group_id,
        test_user_uuid,
    )


class TestRecordPlacementTimeout:
    async def test_unplaced_session_goes_to_rescheduling_with_a_count(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        creating_kubernetes_session: SessionId,
    ) -> None:
        record = await db_source.record_placement_timeout(
            creating_kubernetes_session, "unschedulable", "no node fits"
        )

        assert record is not None
        assert record.attempts == 1
        row = await _read(db_with_cleanup, creating_kubernetes_session)
        assert row.status == SessionStatus.RESCHEDULING
        assert row.status_info == "placement-timeout"
        assert row.status_data is not None
        assert row.status_data["placement_timeout"]["attempts"] == 1
        assert row.status_data["placement_timeout"]["message"] == "no node fits"

    async def test_count_grows_across_attempts(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        creating_kubernetes_session: SessionId,
    ) -> None:
        await db_source.record_placement_timeout(creating_kubernetes_session, "r", None)
        await _set_status(db_with_cleanup, creating_kubernetes_session, SessionStatus.CREATING)

        record = await db_source.record_placement_timeout(creating_kubernetes_session, "r", None)

        assert record is not None
        assert record.attempts == 2

    async def test_repeated_event_is_ignored(
        self,
        db_source: ScheduleDBSource,
        creating_kubernetes_session: SessionId,
    ) -> None:
        await db_source.record_placement_timeout(creating_kubernetes_session, "r", None)

        repeated = await db_source.record_placement_timeout(creating_kubernetes_session, "r", None)

        assert repeated is None

    async def test_running_session_is_ignored(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        running_kubernetes_session: SessionId,
    ) -> None:
        record = await db_source.record_placement_timeout(running_kubernetes_session, "r", None)

        assert record is None
        row = await _read(db_with_cleanup, running_kubernetes_session)
        assert row.status == SessionStatus.RUNNING

    async def test_docker_session_is_ignored(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        creating_docker_session: SessionId,
    ) -> None:
        record = await db_source.record_placement_timeout(creating_docker_session, "r", None)

        assert record is None
        row = await _read(db_with_cleanup, creating_docker_session)
        assert row.status == SessionStatus.CREATING


class TestCancelReschedulingSessions:
    async def test_rescheduling_session_is_cancelled(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        creating_kubernetes_session: SessionId,
    ) -> None:
        await db_source.record_placement_timeout(creating_kubernetes_session, "r", None)

        cancelled = await db_source.cancel_rescheduling_sessions(
            [creating_kubernetes_session], "placement-timeout"
        )

        assert cancelled == [creating_kubernetes_session]
        row = await _read(db_with_cleanup, creating_kubernetes_session)
        assert row.status == SessionStatus.CANCELLED
        assert row.status_info == "placement-timeout"

    async def test_session_in_another_status_is_left_alone(
        self,
        db_source: ScheduleDBSource,
        running_kubernetes_session: SessionId,
    ) -> None:
        cancelled = await db_source.cancel_rescheduling_sessions(
            [running_kubernetes_session], "placement-timeout"
        )

        assert cancelled == []
