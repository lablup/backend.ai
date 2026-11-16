"""Runs the session group retention boundary backfill against a real database and
reads the stamped ``deleted_at`` back."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.schema.deployment import IntOrPercent, ReplicaGroupRolloutSpec
from ai.backend.manager.data.deployment.types import ReplicaGroupLifecycle
from ai.backend.manager.data.session_group.types import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.models.alembic.versions import (
    afcdb49cc729_stamp_deleted_at_on_unserved_session_groups as revision,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
    KeyPairResourcePolicyRow,
    ResourceGroupRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    EndpointRow,
    SessionGroupRow,
    ReplicaGroupRow,
]

_CREATED_AT = datetime(2025, 1, 1, tzinfo=UTC)
_DRAINED_AT = datetime(2025, 6, 1, tzinfo=UTC)


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@dataclass
class _Scope:
    domain_name: str
    domain_id: DomainID
    project_id: uuid.UUID
    user_uuid: uuid.UUID
    resource_group_name: str


async def _seed_scope(db: ExtendedAsyncSAEngine) -> _Scope:
    scope = _Scope(
        domain_name=f"domain-{uuid.uuid4().hex[:8]}",
        domain_id=DomainID(uuid.uuid4()),
        project_id=uuid.uuid4(),
        user_uuid=uuid.uuid4(),
        resource_group_name=f"rg-{uuid.uuid4().hex[:8]}",
    )
    user_policy = f"user-policy-{uuid.uuid4().hex[:8]}"
    project_policy = f"project-policy-{uuid.uuid4().hex[:8]}"
    async with db.begin_session() as sess:
        sess.add(
            UserResourcePolicyRow(
                name=user_policy,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        sess.add(
            ProjectResourcePolicyRow(
                name=project_policy,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=0,
            )
        )
        sess.add(
            DomainRow(
                id=scope.domain_id,
                name=scope.domain_name,
                description=None,
                is_active=True,
            )
        )
        sess.add(
            ResourceGroupRow(
                name=scope.resource_group_name,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
            )
        )
        sess.add(
            UserRow(
                uuid=scope.user_uuid,
                username=f"user-{uuid.uuid4().hex[:8]}",
                email=f"{uuid.uuid4().hex[:8]}@example.com",
                password=PasswordInfo(
                    password="pw",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=100_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name="User",
                description="",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=scope.domain_name,
                role=UserRole.USER,
                resource_policy=user_policy,
                domain_id=scope.domain_id,
            )
        )
        sess.add(
            ProjectRow(
                id=scope.project_id,
                name=f"project-{uuid.uuid4().hex[:8]}",
                description=None,
                is_active=True,
                domain_name=scope.domain_name,
                resource_policy=project_policy,
            )
        )
    return scope


async def _add_group(
    db: ExtendedAsyncSAEngine,
    scope: _Scope,
    *,
    deleted_at: datetime | None = None,
) -> SessionGroupID:
    group_id = SessionGroupID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            SessionGroupRow(
                id=group_id,
                domain_id=scope.domain_id,
                project_id=scope.project_id,
                owner_user_id=scope.user_uuid,
                placement_direction=SessionGroupPlacementDirection.SPREAD,
                placement_enforcement=SessionGroupPlacementEnforcement.PREFERRED,
                created_at=_CREATED_AT,
                deleted_at=deleted_at,
            )
        )
    return group_id


async def _add_endpoint(db: ExtendedAsyncSAEngine, scope: _Scope) -> DeploymentID:
    endpoint_id = DeploymentID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            EndpointRow(
                id=endpoint_id,
                name=f"endpoint-{uuid.uuid4().hex[:8]}",
                created_user=scope.user_uuid,
                session_owner=scope.user_uuid,
                domain=scope.domain_name,
                project=scope.project_id,
                resource_group=scope.resource_group_name,
                lifecycle_stage=EndpointLifecycle.READY,
                replicas=0,
            )
        )
    return endpoint_id


async def _add_replica_groups(
    db: ExtendedAsyncSAEngine,
    endpoint_id: DeploymentID,
    group_id: SessionGroupID,
    lifecycles: Sequence[ReplicaGroupLifecycle],
) -> None:
    async with db.begin_session() as sess:
        for lifecycle in lifecycles:
            sess.add(
                ReplicaGroupRow(
                    id=ReplicaGroupID(uuid.uuid4()),
                    deployment_id=endpoint_id,
                    session_group_id=group_id,
                    lifecycle=lifecycle,
                    rollout=ReplicaGroupRolloutSpec(
                        max_surge=IntOrPercent(count=1),
                        max_unavailable=IntOrPercent(count=0),
                    ),
                    updated_at=_DRAINED_AT,
                )
            )


async def _stamp(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(revision.stamp_unserved_groups)


async def _deleted_at(db: ExtendedAsyncSAEngine, group_id: SessionGroupID) -> datetime | None:
    async with db.begin_readonly_session() as sess:
        return await sess.scalar(
            sa.select(SessionGroupRow.deleted_at).where(SessionGroupRow.id == group_id)
        )


class TestStampUnservedGroups:
    async def test_a_group_never_owned_by_a_deployment_keeps_a_null_boundary(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        scope = await _seed_scope(db)
        group_id = await _add_group(db, scope)

        await _stamp(db)

        assert await _deleted_at(db, group_id) is None

    async def test_a_group_of_a_live_replica_group_keeps_a_null_boundary(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        scope = await _seed_scope(db)
        endpoint_id = await _add_endpoint(db, scope)
        group_id = await _add_group(db, scope)
        await _add_replica_groups(db, endpoint_id, group_id, [ReplicaGroupLifecycle.STABLE])

        await _stamp(db)

        assert await _deleted_at(db, group_id) is None

    async def test_a_group_of_terminal_replica_groups_takes_the_last_transition(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        scope = await _seed_scope(db)
        endpoint_id = await _add_endpoint(db, scope)
        group_id = await _add_group(db, scope)
        await _add_replica_groups(
            db,
            endpoint_id,
            group_id,
            [ReplicaGroupLifecycle.DRAINED, ReplicaGroupLifecycle.FAILED],
        )

        await _stamp(db)

        assert await _deleted_at(db, group_id) == _DRAINED_AT

    async def test_a_stamped_group_is_left_alone(self, db: ExtendedAsyncSAEngine) -> None:
        scope = await _seed_scope(db)
        endpoint_id = await _add_endpoint(db, scope)
        stamped_at = _CREATED_AT + timedelta(days=1)
        group_id = await _add_group(db, scope, deleted_at=stamped_at)
        await _add_replica_groups(db, endpoint_id, group_id, [ReplicaGroupLifecycle.DRAINED])

        await _stamp(db)

        assert await _deleted_at(db, group_id) == stamped_at

    async def test_running_it_twice_leaves_the_same_values(self, db: ExtendedAsyncSAEngine) -> None:
        scope = await _seed_scope(db)
        endpoint_id = await _add_endpoint(db, scope)
        group_id = await _add_group(db, scope)
        await _add_replica_groups(db, endpoint_id, group_id, [ReplicaGroupLifecycle.DRAINED])

        await _stamp(db)
        once = await _deleted_at(db, group_id)

        await _stamp(db)

        assert await _deleted_at(db, group_id) == once
