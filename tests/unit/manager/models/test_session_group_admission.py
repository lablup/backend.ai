"""The admission and member count of a session group against a real database (BEP-1083)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import BinarySize
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.session_group import (
    InvalidSessionGroupAdmission,
    SessionGroupAdmissionInUse,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session_group.creators import SessionGroupCreator
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_group.updaters import SessionGroupUpdater
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.sokovan_core.types.policy import (
    SessionGroupAdmission,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
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
    SessionRow,
]


@dataclass
class _Scope:
    domain_id: DomainID
    domain_name: str
    project_id: ProjectID
    owner_user_id: UserID
    resource_group_id: ResourceGroupID
    resource_group_name: str


@pytest.fixture
async def db(database_connection: ExtendedAsyncSAEngine) -> AsyncIterator[ExtendedAsyncSAEngine]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def scope(db: ExtendedAsyncSAEngine) -> _Scope:
    domain = DomainRow(id=DomainID(uuid.uuid4()), name=f"test-{uuid.uuid4().hex[:8]}")
    resource_group = ResourceGroupRow(
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
        username=f"testuser-{uuid.uuid4().hex[:8]}",
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        domain_name=domain.name,
        resource_policy=user_policy.name,
        domain_id=domain.id,
    )
    project = ProjectRow(
        id=uuid.uuid4(),
        name=f"test-group-{uuid.uuid4().hex[:8]}",
        domain_name=domain.name,
        resource_policy=project_policy.name,
    )
    async with db.begin_session() as sess:
        sess.add_all([domain, resource_group, user_policy, project_policy])
        await sess.flush()
        sess.add_all([user, project])
    return _Scope(
        domain_id=DomainID(domain.id),
        domain_name=domain.name,
        project_id=ProjectID(project.id),
        owner_user_id=UserID(user.uuid),
        resource_group_id=ResourceGroupID(resource_group.id),
        resource_group_name=resource_group.name,
    )


@pytest.fixture
async def independent_group(db: ExtendedAsyncSAEngine, scope: _Scope) -> SessionGroupID:
    group_id = SessionGroupID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            SessionGroupRow(
                id=group_id,
                domain_id=scope.domain_id,
                project_id=scope.project_id,
                owner_user_id=scope.owner_user_id,
                placement_direction=SessionGroupPlacementDirection.SPREAD,
                placement_enforcement=SessionGroupPlacementEnforcement.PREFERRED,
            )
        )
    return group_id


@pytest.fixture
async def group_with_a_pending_member(
    db: ExtendedAsyncSAEngine, scope: _Scope, independent_group: SessionGroupID
) -> SessionGroupID:
    session_id = uuid.uuid4()
    async with db.begin_session() as sess:
        sess.add(
            SessionRow(
                id=session_id,
                name=f"test-{session_id}",
                user_uuid=scope.owner_user_id,
                group_id=scope.project_id,
                domain_id=scope.domain_id,
                domain_name=scope.domain_name,
                resource_group_id=scope.resource_group_id,
                scaling_group_name=scope.resource_group_name,
                status=SessionStatus.PENDING,
                vfolder_mounts=[],
                session_group_id=independent_group,
            )
        )
    return independent_group


def _to_all_or_none(group_id: SessionGroupID, member_count: int | None) -> SessionGroupUpdater:
    return SessionGroupUpdater(
        session_group_id=group_id,
        admission=OptionalState.update(SessionGroupAdmission.ALL_OR_NONE),
        member_count=TriState.update(member_count)
        if member_count is not None
        else TriState[int].nop(),
    )


class TestSessionGroupCreatorAdmission:
    async def test_an_all_or_none_group_without_a_member_count_is_rejected(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        creator = SessionGroupCreator(
            project_id=scope.project_id,
            owner_user_id=scope.owner_user_id,
            placement_direction=SessionGroupPlacementDirection.SPREAD,
            placement_enforcement=SessionGroupPlacementEnforcement.STRICT,
            admission=SessionGroupAdmission.ALL_OR_NONE,
            member_count=None,
        )

        with pytest.raises(InvalidSessionGroupAdmission):
            async with V2DBOpsProvider(db).write_ops() as w:
                await w.create_entity(creator)


class TestSessionGroupUpdaterAdmission:
    async def test_admission_and_member_count_change_together(
        self, db: ExtendedAsyncSAEngine, independent_group: SessionGroupID
    ) -> None:
        async with V2DBOpsProvider(db).write_ops() as w:
            data = await w.update_data(_to_all_or_none(independent_group, 3))

        assert data is not None
        assert data.admission is SessionGroupAdmission.ALL_OR_NONE
        assert data.member_count == 3

    async def test_all_or_none_without_a_member_count_is_rejected(
        self, db: ExtendedAsyncSAEngine, independent_group: SessionGroupID
    ) -> None:
        with pytest.raises(InvalidSessionGroupAdmission):
            async with V2DBOpsProvider(db).write_ops() as w:
                await w.update_data(_to_all_or_none(independent_group, None))

    async def test_admission_does_not_change_while_a_member_is_pending(
        self, db: ExtendedAsyncSAEngine, group_with_a_pending_member: SessionGroupID
    ) -> None:
        with pytest.raises(SessionGroupAdmissionInUse):
            async with V2DBOpsProvider(db).write_ops() as w:
                await w.update_data(_to_all_or_none(group_with_a_pending_member, 2))

    async def test_placement_changes_while_a_member_is_pending(
        self, db: ExtendedAsyncSAEngine, group_with_a_pending_member: SessionGroupID
    ) -> None:
        updater = SessionGroupUpdater(
            session_group_id=group_with_a_pending_member,
            placement_direction=OptionalState.update(SessionGroupPlacementDirection.PACK),
        )

        async with V2DBOpsProvider(db).write_ops() as w:
            data = await w.update_data(updater)

        assert data is not None
        assert data.placement_direction is SessionGroupPlacementDirection.PACK
        assert data.admission is SessionGroupAdmission.INDEPENDENT
