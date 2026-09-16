"""Verifies the vfolder graph backfill migration against a real database.

Static analysis does not reach the migration's SQL, so the data migration is exercised
here: folders go in, the migration runs, and the graph rows it wrote are read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import QuotaScopeID, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.vfolder.types import (
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.alembic.versions.dafe06a6c763_put_vfolders_in_the_graph import (
    put_vfolders_in_the_graph,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    VFolderRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
]


@dataclass
class Fixture:
    """A user with a personal project, and a team project, both with graph nodes."""

    domain_name: DomainName
    user_id: uuid.UUID
    personal_project_id: uuid.UUID
    team_project_id: uuid.UUID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def fixture(db: ExtendedAsyncSAEngine) -> Fixture:
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
    user_id = uuid.uuid4()
    personal_project_id = uuid.uuid4()
    team_project_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            DomainRow(
                id=domain_id,
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
        )
        session.add(
            ProjectResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
        )
        session.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        session.add(
            UserRow(
                uuid=user_id,
                username="alice",
                email=f"{uuid.uuid4().hex[:8]}@test.local",
                password=PasswordInfo(
                    password="test-password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1_000,
                    salt_size=32,
                ),
                need_password_change=False,
                domain_id=domain_id,
                domain_name=domain_name,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                resource_policy="default",
            )
        )
        await session.commit()
    async with db.begin_session() as session:
        for project_id, name, project_type, creator in (
            (personal_project_id, "alice", ProjectType.PERSONAL, user_id),
            (team_project_id, "team", ProjectType.GENERAL, None),
        ):
            session.add(
                ProjectRow(
                    id=project_id,
                    name=name,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    resource_policy="default",
                    type=project_type,
                    creator_id=creator,
                )
            )
            session.add(VirtualEntityRow(entity_type="project", entity_id=project_id))
        await session.commit()
    return Fixture(
        domain_name=domain_name,
        user_id=user_id,
        personal_project_id=personal_project_id,
        team_project_id=team_project_id,
    )


async def _add_vfolder(
    db: ExtendedAsyncSAEngine,
    fx: Fixture,
    *,
    name: str,
    ownership_type: VFolderOwnershipType,
    user: uuid.UUID | None,
    group: uuid.UUID,
    with_node: bool = False,
) -> uuid.UUID:
    vfolder_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            VFolderRow(
                id=vfolder_id,
                name=name,
                domain_name=fx.domain_name,
                quota_scope_id=QuotaScopeID.parse(f"user:{fx.user_id}"),
                host="local",
                creator="alice@test.local",
                creator_id=fx.user_id,
                ownership_type=ownership_type,
                user=user,
                group=group,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
        )
        await session.commit()
    if with_node:
        async with db.begin_session() as session:
            node = VirtualEntityRow(entity_type="vfolder", entity_id=vfolder_id)
            session.add(node)
            await session.flush()
            session.add(
                ScopeBindingRow(
                    virtual_entity_id=node.id, scope_entity_id=node.id, permission_cap=None
                )
            )
            await session.commit()
    return vfolder_id


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(put_vfolders_in_the_graph)


async def _node_of(
    db: ExtendedAsyncSAEngine, entity_type: str, entity_id: uuid.UUID
) -> uuid.UUID | None:
    async with db.begin_readonly_session() as session:
        node: uuid.UUID | None = await session.scalar(
            sa.select(VirtualEntityRow.id).where(
                VirtualEntityRow.entity_type == entity_type,
                VirtualEntityRow.entity_id == entity_id,
            )
        )
        return node


async def _owner_nodes(db: ExtendedAsyncSAEngine, node: uuid.UUID) -> list[uuid.UUID]:
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(EntityMembershipRow.virtual_entity_id).where(
                        EntityMembershipRow.member_entity_id == node
                    )
                )
            ).all()
        )


async def _governing_nodes(db: ExtendedAsyncSAEngine, node: uuid.UUID) -> list[uuid.UUID]:
    async with db.begin_readonly_session() as session:
        return list(
            (
                await session.scalars(
                    sa.select(ScopeBindingRow.scope_entity_id).where(
                        ScopeBindingRow.virtual_entity_id == node
                    )
                )
            ).all()
        )


class TestPutVFoldersInTheGraph:
    async def test_a_personal_folder_is_put_under_its_personal_project(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        vfolder_id = await _add_vfolder(
            db,
            fixture,
            name="mine",
            ownership_type=VFolderOwnershipType.USER,
            user=fixture.user_id,
            group=fixture.personal_project_id,
        )

        await _run(db)

        folder_node = await _node_of(db, "vfolder", vfolder_id)
        project_node = await _node_of(db, "project", fixture.personal_project_id)
        assert folder_node is not None
        assert set(await _owner_nodes(db, folder_node)) == {folder_node, project_node}
        assert set(await _governing_nodes(db, folder_node)) == {folder_node, project_node}

    async def test_a_project_folder_is_put_under_its_project(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        vfolder_id = await _add_vfolder(
            db,
            fixture,
            name="teams",
            ownership_type=VFolderOwnershipType.GROUP,
            user=None,
            group=fixture.team_project_id,
        )

        await _run(db)

        folder_node = await _node_of(db, "vfolder", vfolder_id)
        project_node = await _node_of(db, "project", fixture.team_project_id)
        assert folder_node is not None
        assert set(await _owner_nodes(db, folder_node)) == {folder_node, project_node}
        assert set(await _governing_nodes(db, folder_node)) == {folder_node, project_node}

    async def test_a_node_bound_only_to_itself_gains_its_project(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        vfolder_id = await _add_vfolder(
            db,
            fixture,
            name="mine",
            ownership_type=VFolderOwnershipType.USER,
            user=fixture.user_id,
            group=fixture.personal_project_id,
            with_node=True,
        )
        folder_node = await _node_of(db, "vfolder", vfolder_id)
        assert folder_node is not None

        await _run(db)

        project_node = await _node_of(db, "project", fixture.personal_project_id)
        assert await _node_of(db, "vfolder", vfolder_id) == folder_node
        assert set(await _governing_nodes(db, folder_node)) == {folder_node, project_node}

    async def test_running_twice_changes_nothing(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        vfolder_id = await _add_vfolder(
            db,
            fixture,
            name="teams",
            ownership_type=VFolderOwnershipType.GROUP,
            user=None,
            group=fixture.team_project_id,
        )

        await _run(db)
        await _run(db)

        folder_node = await _node_of(db, "vfolder", vfolder_id)
        assert folder_node is not None
        assert len(await _owner_nodes(db, folder_node)) == 2
        assert len(await _governing_nodes(db, folder_node)) == 2
