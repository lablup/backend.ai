from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.session_group import SessionGroupID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.session_group.types import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


@dataclass
class _OwnershipScope:
    domain_id: DomainID
    domain_name: str
    project_id: ProjectID
    owner_user_id: UserID
    resource_group_id: ResourceGroupID
    resource_group_name: str


class TestSessionGroupSchema:
    """Column contracts the scheduler and the retention sweep rely on."""

    def test_placement_axes_are_separate_columns(self) -> None:
        columns = SessionGroupRow.__table__.columns

        assert columns["placement_direction"].nullable is False
        assert columns["placement_enforcement"].nullable is False

    def test_ownership_axes_match_sessions_and_endpoints(self) -> None:
        columns = SessionGroupRow.__table__.columns

        targets = {
            name: {fk.target_fullname for fk in columns[name].foreign_keys}
            for name in ("domain_id", "project_id", "owner_user_id")
        }

        assert targets == {
            "domain_id": {"domains.id"},
            "project_id": {"groups.id"},
            "owner_user_id": {"users.uuid"},
        }
        assert all(not columns[name].nullable for name in targets)

    def test_owner_cannot_be_removed_before_their_groups(self) -> None:
        # The purge settles a user's groups explicitly (transfer on delegation,
        # delete otherwise); the database must not silently drop them instead.
        (owner_fk,) = list(SessionGroupRow.__table__.columns["owner_user_id"].foreign_keys)

        assert owner_fk.ondelete == "RESTRICT"

    def test_group_has_no_name_column(self) -> None:
        assert "name" not in SessionGroupRow.__table__.columns

    def test_session_link_is_nullable_indexed_and_set_null_on_delete(self) -> None:
        column = SessionRow.__table__.columns["session_group_id"]
        (foreign_key,) = list(column.foreign_keys)

        assert column.nullable is True
        assert foreign_key.target_fullname == "session_groups.id"
        assert foreign_key.ondelete == "SET NULL"
        assert any(list(index.columns) == [column] for index in SessionRow.__table__.indexes), (
            "the per-agent membership query joins on this column"
        )

    def test_replica_group_link_is_mandatory(self) -> None:
        column = ReplicaGroupRow.__table__.columns["session_group_id"]
        (foreign_key,) = list(column.foreign_keys)

        assert column.nullable is False
        assert foreign_key.target_fullname == "session_groups.id"


class TestSessionGroupRow:
    @pytest.fixture
    async def db(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                SessionGroupRow,
                SessionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scope(self, db: ExtendedAsyncSAEngine) -> AsyncIterator[_OwnershipScope]:
        domain = DomainRow(id=DomainID(uuid.uuid4()), name=f"test-{uuid.uuid4().hex[:8]}")
        scaling_group = ScalingGroupRow(
            id=ResourceGroupID(uuid.uuid4()),
            name=f"test-sg-{uuid.uuid4().hex[:8]}",
            driver="static",
            scheduler="fifo",
        )
        user_policy = UserResourcePolicyRow(
            name=f"{uuid.uuid4()}",
            max_vfolder_count=10,
            max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )
        project_policy = ProjectResourcePolicyRow(
            name=f"{uuid.uuid4()}",
            max_vfolder_count=10,
            max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
            max_network_count=5,
        )
        user = UserRow(
            uuid=uuid.uuid4(),
            email=f"user-{uuid.uuid4().hex[:8]}@example.com",
            domain_name=domain.name,
            resource_policy=user_policy.name,
        )
        project = GroupRow(
            id=uuid.uuid4(),
            name=f"test-group-{uuid.uuid4().hex[:8]}",
            domain_name=domain.name,
            domain_id=domain.id,
            resource_policy=project_policy.name,
        )

        async with db.begin_session() as sess:
            sess.add_all([domain, scaling_group, user_policy, project_policy])
            await sess.flush()
            sess.add_all([user, project])
            await sess.flush()

        yield _OwnershipScope(
            domain_id=DomainID(domain.id),
            domain_name=domain.name,
            project_id=ProjectID(project.id),
            owner_user_id=UserID(user.uuid),
            resource_group_id=ResourceGroupID(scaling_group.id),
            resource_group_name=scaling_group.name,
        )

    async def test_placement_policy_round_trips(
        self, db: ExtendedAsyncSAEngine, scope: _OwnershipScope
    ) -> None:
        group_id = SessionGroupID(uuid.uuid4())
        async with db.begin_session() as sess:
            sess.add(_make_group(group_id, scope, SessionGroupPlacementDirection.SPREAD))

        async with db.begin_readonly_session() as sess:
            row = (
                await sess.execute(sa.select(SessionGroupRow).where(SessionGroupRow.id == group_id))
            ).scalar_one()

        assert row.placement_direction is SessionGroupPlacementDirection.SPREAD
        assert row.placement_enforcement is SessionGroupPlacementEnforcement.PREFERRED
        assert row.domain_id == scope.domain_id
        assert row.project_id == scope.project_id
        assert row.owner_user_id == scope.owner_user_id
        assert row.deleted_at is None

    async def test_session_defaults_to_no_group(
        self, db: ExtendedAsyncSAEngine, scope: _OwnershipScope
    ) -> None:
        session_id = uuid.uuid4()
        async with db.begin_session() as sess:
            sess.add(_make_session(session_id, scope, session_group_id=None))

        async with db.begin_readonly_session() as sess:
            row = (
                await sess.execute(sa.select(SessionRow).where(SessionRow.id == session_id))
            ).scalar_one()

        assert row.session_group_id is None

    async def test_deleting_group_unbinds_members_without_removing_them(
        self, db: ExtendedAsyncSAEngine, scope: _OwnershipScope
    ) -> None:
        group_id = SessionGroupID(uuid.uuid4())
        session_id = uuid.uuid4()
        async with db.begin_session() as sess:
            sess.add(_make_group(group_id, scope, SessionGroupPlacementDirection.PACK))
            await sess.flush()
            sess.add(_make_session(session_id, scope, session_group_id=group_id))

        async with db.begin_session() as sess:
            await sess.execute(sa.delete(SessionGroupRow).where(SessionGroupRow.id == group_id))

        async with db.begin_readonly_session() as sess:
            row = (
                await sess.execute(sa.select(SessionRow).where(SessionRow.id == session_id))
            ).scalar_one()

        assert row.session_group_id is None


def _make_group(
    group_id: SessionGroupID,
    scope: _OwnershipScope,
    direction: SessionGroupPlacementDirection,
) -> SessionGroupRow:
    return SessionGroupRow(
        id=group_id,
        domain_id=scope.domain_id,
        project_id=scope.project_id,
        owner_user_id=scope.owner_user_id,
        placement_direction=direction,
        placement_enforcement=SessionGroupPlacementEnforcement.PREFERRED,
    )


def _make_session(
    session_id: uuid.UUID,
    scope: _OwnershipScope,
    session_group_id: SessionGroupID | None,
) -> SessionRow:
    return SessionRow(
        id=session_id,
        name=f"test-{session_id}",
        user_uuid=scope.owner_user_id,
        group_id=scope.project_id,
        domain_id=scope.domain_id,
        domain_name=scope.domain_name,
        resource_group_id=scope.resource_group_id,
        scaling_group_name=scope.resource_group_name,
        status=SessionStatus.PENDING,
        occupying_slots=ResourceSlot(),
        requested_slots=ResourceSlot(),
        vfolder_mounts=[],
        session_group_id=session_group_id,
    )
