"""``ScheduleDBSource.search_session_groups`` with the searcher a session enqueue builds."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.schema.deployment import IntOrPercent, ReplicaGroupRolloutSpec
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.session_group.types import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_group.searchers import SessionGroupSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    ResourceSlotEntry,
    SessionResourceSpec,
    SessionSchedulingSpec,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import _SCHEDULER_ROWS


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """The scheduler table set plus the tables a deployment's group is held through."""
    async with with_tables(database_connection, [*_SCHEDULER_ROWS, EndpointRow, ReplicaGroupRow]):
        yield database_connection


@pytest.fixture
async def session_group_id(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain_id: DomainID,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
) -> SessionGroupID:
    group_id = SessionGroupID(uuid.uuid4())
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            SessionGroupRow(
                id=group_id,
                domain_id=test_domain_id,
                project_id=ProjectID(test_group_id),
                owner_user_id=UserID(test_user_uuid),
                placement_direction=SessionGroupPlacementDirection.SPREAD,
                placement_enforcement=SessionGroupPlacementEnforcement.PREFERRED,
            )
        )
    return group_id


@pytest.fixture
async def deleted(
    db_with_cleanup: ExtendedAsyncSAEngine,
    session_group_id: SessionGroupID,
) -> None:
    async with db_with_cleanup.begin_session() as db_sess:
        await db_sess.execute(
            sa.update(SessionGroupRow)
            .where(SessionGroupRow.id == session_group_id)
            .values(deleted_at=datetime.now(UTC))
        )


@pytest.fixture
async def held_by_replica_group(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain: DomainFixtureData,
    test_scaling_group_name: str,
    test_group_id: uuid.UUID,
    test_user_uuid: uuid.UUID,
    session_group_id: SessionGroupID,
) -> None:
    endpoint_id = uuid.uuid4()
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            EndpointRow(
                id=endpoint_id,
                name=f"test-endpoint-{endpoint_id.hex[:8]}",
                created_user=test_user_uuid,
                session_owner=test_user_uuid,
                domain=test_domain.domain_name,
                project=test_group_id,
                resource_group=test_scaling_group_name,
                desired_replicas=1,
                url=f"http://test-{endpoint_id.hex[:8]}.example.com",
                open_to_public=False,
                lifecycle_stage=EndpointLifecycle.READY,
            )
        )
        await db_sess.flush()
        db_sess.add(
            ReplicaGroupRow(
                id=uuid.uuid4(),
                deployment_id=endpoint_id,
                session_group_id=session_group_id,
                lifecycle=ReplicaGroupLifecycle.STABLE,
                scaling_status=ReplicaGroupScalingStatus.STABLE,
                rollout=ReplicaGroupRolloutSpec(
                    max_surge=IntOrPercent(count=1),
                    max_unavailable=IntOrPercent(count=0),
                ),
            )
        )


def _action(session_group_id: SessionGroupID, project_id: uuid.UUID) -> EnqueueSessionAction:
    """An enqueue into ``project_id`` naming the group."""
    return EnqueueSessionAction(
        project_id=ProjectID(project_id),
        session_name="grouped",
        session_type=SessionTypes.INTERACTIVE,
        image_id=uuid.uuid4(),
        resource=SessionResourceSpec(
            entries=[ResourceSlotEntry(resource_type="cpu", quantity="1")],
            resource_group_id=ResourceGroupID(uuid.uuid4()),
        ),
        scheduling=SessionSchedulingSpec(),
        session_group_id=session_group_id,
        group_id=project_id,
    )


def _owned_searcher(
    session_group_id: SessionGroupID, owner_user_id: UserID, project_id: uuid.UUID
) -> SessionGroupSearcher:
    """The searcher for a group ``owner_user_id`` owns in ``project_id``."""
    searcher = _action(session_group_id, project_id).to_owned_session_group_searcher(owner_user_id)
    assert searcher is not None
    return searcher


def _held_searcher(
    session_group_id: SessionGroupID, owner_user_id: UserID, project_id: uuid.UUID
) -> SessionGroupSearcher:
    """The searcher for that owned group, only when a replica group holds it."""
    searcher = _action(session_group_id, project_id).to_held_session_group_searcher(owner_user_id)
    assert searcher is not None
    return searcher


class TestSearchSessionGroups:
    async def test_answers_the_owners_group_in_the_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        session_group_id: SessionGroupID,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        groups = await db_source.search_session_groups(
            _owned_searcher(session_group_id, UserID(test_user_uuid), test_group_id)
        )

        assert [g.id for g in groups] == [session_group_id]

    async def test_answers_nothing_for_a_missing_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        groups = await db_source.search_session_groups(
            _owned_searcher(SessionGroupID(uuid.uuid4()), UserID(test_user_uuid), test_group_id)
        )

        assert groups == []

    async def test_answers_nothing_for_another_owner(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group_id: uuid.UUID,
        session_group_id: SessionGroupID,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        groups = await db_source.search_session_groups(
            _owned_searcher(session_group_id, UserID(uuid.uuid4()), test_group_id)
        )

        assert groups == []

    async def test_answers_nothing_for_another_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        session_group_id: SessionGroupID,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        groups = await db_source.search_session_groups(
            _owned_searcher(session_group_id, UserID(test_user_uuid), uuid.uuid4())
        )

        assert groups == []

    async def test_answers_nothing_for_a_deleted_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        session_group_id: SessionGroupID,
        deleted: None,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        groups = await db_source.search_session_groups(
            _owned_searcher(session_group_id, UserID(test_user_uuid), test_group_id)
        )

        assert groups == []

    async def test_the_owned_searcher_answers_a_group_a_replica_group_holds(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        session_group_id: SessionGroupID,
        held_by_replica_group: None,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        groups = await db_source.search_session_groups(
            _owned_searcher(session_group_id, UserID(test_user_uuid), test_group_id)
        )

        assert [g.id for g in groups] == [session_group_id]

    async def test_the_held_searcher_answers_a_group_a_replica_group_holds(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        session_group_id: SessionGroupID,
        held_by_replica_group: None,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        groups = await db_source.search_session_groups(
            _held_searcher(session_group_id, UserID(test_user_uuid), test_group_id)
        )

        assert [g.id for g in groups] == [session_group_id]

    async def test_the_held_searcher_answers_nothing_for_a_group_no_replica_group_holds(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        session_group_id: SessionGroupID,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        groups = await db_source.search_session_groups(
            _held_searcher(session_group_id, UserID(test_user_uuid), test_group_id)
        )

        assert groups == []
