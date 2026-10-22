"""Runs the image project-edge cleanup against a real database and reads the graph rows
back.

Static analysis does not reach the revision's SQL, so the edges the graph backfill wrote
are seeded here and the revision is run over them.
"""

from __future__ import annotations

import importlib.util
import pathlib
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.image import ImageEntityType, ImageID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.alembic.versions import (
    d17b4e9c25a8_take_images_out_of_personal_projects as revision,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

_REGISTRY_NAME = "cr.test.io"
_POLICY_NAME = "default"

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    ProjectRow,
    ContainerRegistryRow,
    ImageRow,
    VirtualEntityRow,
    EntityMembershipRow,
    ScopeBindingRow,
]


@dataclass
class _Seeded:
    """The nodes of one catalog, wired as the graph backfill wired them."""

    registry: VirtualEntityID
    personal_project: VirtualEntityID
    committed: VirtualEntityID
    general: VirtualEntityID
    shared: VirtualEntityID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def domain_id(db: ExtendedAsyncSAEngine) -> DomainID:
    domain_id = DomainID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            DomainRow(
                id=domain_id,
                name=DomainName("test-domain"),
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[_REGISTRY_NAME],
                dotfiles=b"\x90",
            )
        )
        session.add(
            UserResourcePolicyRow(
                name=_POLICY_NAME,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=1,
                max_customized_image_count=10,
            )
        )
        session.add(
            ProjectResourcePolicyRow(
                name=_POLICY_NAME,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=0,
            )
        )
        await session.commit()
    return domain_id


async def _add_node(
    db: ExtendedAsyncSAEngine, entity_type: EntityType, entity_id: uuid.UUID
) -> VirtualEntityID:
    async with db.begin_session() as session:
        node = VirtualEntityRow(entity_type=entity_type, entity_id=entity_id)
        session.add(node)
        await session.flush()
        return node.id


async def _add_user(db: ExtendedAsyncSAEngine, domain_id: DomainID) -> UserID:
    user_id = UserID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            UserRow(
                uuid=user_id,
                username=f"user-{user_id.hex[:8]}",
                email=f"{user_id.hex[:8]}@test.io",
                password=PasswordInfo(
                    password="test-password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1_000,
                    salt_size=32,
                ),
                need_password_change=False,
                domain_id=domain_id,
                domain_name="test-domain",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                resource_policy=_POLICY_NAME,
            )
        )
        await session.commit()
    return user_id


async def _add_personal_project(db: ExtendedAsyncSAEngine, user_id: UserID, name: str) -> ProjectID:
    project_id = ProjectID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            ProjectRow(
                id=project_id,
                name=name,
                domain_name="test-domain",
                is_active=True,
                type=ProjectType.PERSONAL,
                creator_id=user_id,
                resource_policy=_POLICY_NAME,
            )
        )
        await session.commit()
    return project_id


async def _add_registry(db: ExtendedAsyncSAEngine) -> ContainerRegistryID:
    registry_id = ContainerRegistryID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(
            ContainerRegistryRow(
                id=registry_id,
                url=f"https://{_REGISTRY_NAME}",
                registry_name=_REGISTRY_NAME,
                type=ContainerRegistryType.DOCKER,
                project="stable",
                is_global=True,
            )
        )
        await session.commit()
    return registry_id


async def _add_image(
    db: ExtendedAsyncSAEngine,
    registry_id: ContainerRegistryID,
    *,
    customized: bool,
    creator_id: UserID | None,
) -> ImageID:
    tag = uuid.uuid4().hex[:8]
    async with db.begin_session() as session:
        row = ImageRow(
            name=f"{_REGISTRY_NAME}/stable/python:{tag}",
            image="python",
            tag=tag,
            registry=_REGISTRY_NAME,
            registry_id=registry_id,
            project="stable",
            architecture="x86_64",
            config_digest=f"sha256:{uuid.uuid4().hex}",
            size_bytes=1000,
            type=ImageType.COMPUTE,
            status=ImageStatus.ALIVE,
            accelerators=None,
            labels={},
            resources={},
            customized=customized,
            creator_id=creator_id,
        )
        session.add(row)
        await session.flush()
        return ImageID(row.id)


async def _own(db: ExtendedAsyncSAEngine, scope: VirtualEntityID, member: VirtualEntityID) -> None:
    """The scope owns and governs the member, as a ``created_in`` edge reads."""
    async with db.begin_session() as session:
        session.add(
            EntityMembershipRow(virtual_entity_id=scope, member_entity_id=member, capped=False)
        )
        session.add(
            ScopeBindingRow(virtual_entity_id=member, scope_entity_id=scope, permission_cap=None)
        )


async def _share(
    db: ExtendedAsyncSAEngine, scope: VirtualEntityID, member: VirtualEntityID
) -> None:
    """The scope holds the member through a capped share instead."""
    async with db.begin_session() as session:
        session.add(
            EntityMembershipRow(virtual_entity_id=scope, member_entity_id=member, capped=True)
        )
        session.add(
            ScopeBindingRow(
                virtual_entity_id=member, scope_entity_id=scope, permission_cap=Permission.READ
            )
        )


@pytest.fixture
async def seeded(db: ExtendedAsyncSAEngine, domain_id: DomainID) -> _Seeded:
    """A registry holding three images: one committed for the user and placed in their
    personal project the way the graph backfill placed it, one general, and one the
    project holds through a share."""
    user_id = await _add_user(db, domain_id)
    registry_id = await _add_registry(db)
    project_id = await _add_personal_project(db, user_id, "owner")
    registry = await _add_node(db, ContainerRegistryEntityType(), registry_id)
    personal_project = await _add_node(db, ProjectEntityType(), project_id)

    committed = await _add_node(
        db,
        ImageEntityType(),
        await _add_image(db, registry_id, customized=True, creator_id=user_id),
    )
    await _own(db, registry, committed)
    await _own(db, personal_project, committed)

    general = await _add_node(
        db,
        ImageEntityType(),
        await _add_image(db, registry_id, customized=False, creator_id=None),
    )
    await _own(db, registry, general)

    shared = await _add_node(
        db,
        ImageEntityType(),
        await _add_image(db, registry_id, customized=True, creator_id=user_id),
    )
    await _own(db, registry, shared)
    await _share(db, personal_project, shared)

    return _Seeded(
        registry=registry,
        personal_project=personal_project,
        committed=committed,
        general=general,
        shared=shared,
    )


async def _owning_scopes(
    db: ExtendedAsyncSAEngine, member: VirtualEntityID
) -> set[VirtualEntityID]:
    """The scopes that own and govern the node, counted only where they do both."""
    async with db.begin_readonly_session() as session:
        owned = set(
            (
                await session.scalars(
                    sa.select(EntityMembershipRow.virtual_entity_id).where(
                        EntityMembershipRow.member_entity_id == member,
                        EntityMembershipRow.capped.is_(False),
                    )
                )
            ).all()
        )
        governed = set(
            (
                await session.scalars(
                    sa.select(ScopeBindingRow.scope_entity_id).where(
                        ScopeBindingRow.virtual_entity_id == member,
                        ScopeBindingRow.permission_cap.is_(None),
                    )
                )
            ).all()
        )
    assert owned == governed
    return owned


async def _sharing_scopes(
    db: ExtendedAsyncSAEngine, member: VirtualEntityID
) -> set[VirtualEntityID]:
    async with db.begin_readonly_session() as session:
        return set(
            (
                await session.scalars(
                    sa.select(EntityMembershipRow.virtual_entity_id).where(
                        EntityMembershipRow.member_entity_id == member,
                        EntityMembershipRow.capped.is_(True),
                    )
                )
            ).all()
        )


async def _upgrade(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(revision.remove_project_edges)


async def _downgrade(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(revision.add_project_edges)


class TestTheRevisionLoadsAsAlembicLoadsIt:
    """Alembic reads a revision file without putting the module in `sys.modules`."""

    async def test_the_module_executes_outside_sys_modules(self) -> None:
        path = pathlib.Path(revision.__file__)
        spec = importlib.util.spec_from_file_location(path.stem, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)

        assert module.revision == revision.revision
        assert module.down_revision == revision.down_revision


class TestTakeImagesOutOfPersonalProjects:
    async def test_a_committed_image_keeps_its_registry_alone(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        await _upgrade(db)

        assert await _owning_scopes(db, seeded.committed) == {seeded.registry}

    async def test_a_general_image_is_left_as_it_stands(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        await _upgrade(db)

        assert await _owning_scopes(db, seeded.general) == {seeded.registry}

    async def test_a_share_of_an_image_to_a_project_is_left_alone(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        await _upgrade(db)

        assert await _sharing_scopes(db, seeded.shared) == {seeded.personal_project}
        assert await _owning_scopes(db, seeded.shared) == {seeded.registry}

    async def test_running_it_twice_leaves_the_same_edges(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        await _upgrade(db)
        once = await _owning_scopes(db, seeded.committed)

        await _upgrade(db)

        assert await _owning_scopes(db, seeded.committed) == once

    async def test_the_downgrade_puts_the_personal_project_back(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        before = await _owning_scopes(db, seeded.committed)
        await _upgrade(db)

        await _downgrade(db)

        assert await _owning_scopes(db, seeded.committed) == before

    async def test_the_downgrade_leaves_a_general_image_out(
        self, db: ExtendedAsyncSAEngine, seeded: _Seeded
    ) -> None:
        await _upgrade(db)

        await _downgrade(db)

        assert await _owning_scopes(db, seeded.general) == {seeded.registry}
