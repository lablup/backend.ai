"""``ScheduleDBSource.get_session_group``: the group a session enqueue names."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.schema.deployment import IntOrPercent, ReplicaGroupRolloutSpec
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.session_group.types import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
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


class TestGetSessionGroup:
    async def test_answers_the_group_with_its_owner_and_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        session_group_id: SessionGroupID,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        group = await db_source.get_session_group(session_group_id)

        assert group.id == session_group_id
        assert group.owner_user_id == test_user_uuid
        assert group.project_id == test_group_id
        assert group.deleted_at is None

    async def test_refuses_a_missing_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        with pytest.raises(EntityNotFoundError):
            await db_source.get_session_group(SessionGroupID(uuid.uuid4()))

    async def test_refuses_a_group_a_replica_group_holds(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        session_group_id: SessionGroupID,
        held_by_replica_group: None,
    ) -> None:
        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        with pytest.raises(EntityNotFoundError):
            await db_source.get_session_group(session_group_id)
