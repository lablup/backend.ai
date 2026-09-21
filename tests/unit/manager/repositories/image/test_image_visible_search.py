"""The one scope a legacy image read is answered from, and the permission check beside it.

These reads take no project, so the scope has to stand for every place the caller's
roles reach: the registries registered in `public`, their personal project, and the
registries their projects are linked to. What the scope returns and what the permission
check answers are asserted against each other, so the two cannot come apart.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.image import ImageEntityType, ImageID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.virtual_entity import OwnCheckKey
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.global_entity.row import GlobalEntityRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.image.scopes import VisibleImageTarget
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.querier import execute_batch_querier
from ai.backend.manager.repositories.ops.v2.permission.read import PermissionReadOps
from ai.backend.testutils.db import with_global_entities, with_tables

_DOMAIN_NAME = "test-visible-image"
_POLICY_NAME = "test-visible-image"


@dataclass(frozen=True)
class Catalog:
    """The caller, an unrelated user, and every image the graph was seeded with."""

    member: UserID
    stranger: UserID
    images: dict[str, ImageID]

    def image_ids(self, *keys: str) -> set[uuid.UUID]:
        return {uuid.UUID(str(self.images[key])) for key in keys}


async def _node(
    sess: AsyncSession, entity_type: EntityType, entity_id: uuid.UUID
) -> VirtualEntityRow:
    """A node as provisioning writes one: it owns and governs itself."""
    row = VirtualEntityRow(entity_type=entity_type, entity_id=entity_id)
    sess.add(row)
    await sess.flush()
    sess.add(EntityMembershipRow(virtual_entity_id=row.id, member_entity_id=row.id, capped=False))
    sess.add(ScopeBindingRow(virtual_entity_id=row.id, scope_entity_id=row.id))
    await sess.flush()
    return row


async def _created_in(sess: AsyncSession, scope: VirtualEntityRow, node: VirtualEntityRow) -> None:
    """What creating the entity in the scope writes: the scope owns it and governs it."""
    sess.add(
        EntityMembershipRow(virtual_entity_id=scope.id, member_entity_id=node.id, capped=False)
    )
    sess.add(ScopeBindingRow(virtual_entity_id=node.id, scope_entity_id=scope.id))
    await sess.flush()


async def _linked_to(sess: AsyncSession, scope: VirtualEntityRow, target: VirtualEntityRow) -> None:
    """What a relation row writes: the scope governs the target under READ, and the
    target holds READ on the scope."""
    sess.add(
        ScopeBindingRow(
            virtual_entity_id=target.id,
            scope_entity_id=scope.id,
            permission_cap=Permission.READ,
        )
    )
    edge = EntityMembershipRow(virtual_entity_id=target.id, member_entity_id=scope.id, capped=True)
    sess.add(edge)
    await sess.flush()
    sess.add(
        EntityMembershipCapRow(membership_id=edge.id, permission=Permission.READ, all_fields=True)
    )
    await sess.flush()


async def _grant_image_read(sess: AsyncSession, scope: VirtualEntityRow, user_id: UserID) -> None:
    """A role in the scope holding image READ, assigned to the user."""
    role = RoleRow(
        name=f"role-{uuid.uuid4().hex[:8]}",
        status=RoleStatus.ACTIVE,
        scope_type=scope.entity_type,
        scope_id=scope.entity_id,
    )
    sess.add(role)
    await sess.flush()
    sess.add(
        PermissionRow(role_id=role.id, entity_type=ImageEntityType(), permission=Permission.READ)
    )
    sess.add(UserRoleRow(user_id=user_id, role_id=role.id))
    await sess.flush()


def _image(name: str, registry_id: uuid.UUID, registry_name: str) -> ImageRow:
    return ImageRow(
        name=f"{registry_name}/test_project/{name}",
        image=name.split(":")[0],
        tag=name.split(":")[1],
        registry=registry_name,
        registry_id=registry_id,
        project="test_project",
        architecture="x86_64",
        config_digest=f"sha256:{uuid.uuid4().hex}",
        size_bytes=1000,
        type=ImageType.COMPUTE,
        status=ImageStatus.ALIVE,
        accelerators=None,
        labels={},
        resources={},
    )


class TestVisibleImageSearch:
    @pytest.fixture
    async def image_db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                ProjectRow,
                ContainerRegistryRow,
                ImageRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
                RoleRow,
                PermissionRow,
                UserRoleRow,
            ],
        ):
            async with with_global_entities(database_connection):
                yield database_connection

    @pytest.fixture
    async def catalog(self, image_db: ExtendedAsyncSAEngine) -> Catalog:
        """Four images: one in a registry registered in `public`, one in the caller's
        personal project, one in a registry linked to a project they are on, and one in
        a registry linked to a project they are not on."""
        member = UserID(uuid.uuid4())
        stranger = UserID(uuid.uuid4())
        joined_project = ProjectID(uuid.uuid4())
        other_project = ProjectID(uuid.uuid4())
        personal_project = ProjectID(uuid.uuid4())

        async with image_db.begin_session() as sess:
            await self._write_accounts(
                sess, [member, stranger], [joined_project, other_project], personal_project, member
            )
            registries = {
                "public": ContainerRegistryID(uuid.uuid4()),
                "joined": ContainerRegistryID(uuid.uuid4()),
                "other": ContainerRegistryID(uuid.uuid4()),
            }
            for key, registry_id in registries.items():
                sess.add(
                    ContainerRegistryRow(
                        id=registry_id,
                        url=f"https://{key}.example.com",
                        registry_name=f"{key}.example.com",
                        type=ContainerRegistryType.DOCKER,
                        project="test_project",
                        is_global=key == "public",
                    )
                )
            rows = {
                "public": _image("python:3.13", registries["public"], "public.example.com"),
                "personal": _image("python:3.12", registries["other"], "other.example.com"),
                "joined": _image("python:3.11", registries["joined"], "joined.example.com"),
                "other": _image("python:3.10", registries["other"], "other.example.com"),
            }
            sess.add_all(list(rows.values()))
            await sess.flush()

            public_node = await self._public_node(sess)
            registry_nodes = {
                key: await _node(sess, ContainerRegistryEntityType(), registry_id)
                for key, registry_id in registries.items()
            }
            project_nodes = {
                "joined": await _node(sess, ProjectEntityType(), joined_project),
                "other": await _node(sess, ProjectEntityType(), other_project),
                "personal": await _node(sess, ProjectEntityType(), personal_project),
            }
            await _node(sess, UserEntityType(), member)
            await _linked_to(sess, project_nodes["joined"], registry_nodes["joined"])
            await _linked_to(sess, project_nodes["other"], registry_nodes["other"])
            await _created_in(sess, public_node, registry_nodes["public"])

            image_nodes = {
                key: await _node(sess, ImageEntityType(), row.id) for key, row in rows.items()
            }
            for key, node in image_nodes.items():
                await _created_in(sess, registry_nodes[self._registry_of(key)], node)
            await _created_in(sess, public_node, image_nodes["public"])
            await _created_in(sess, project_nodes["personal"], image_nodes["personal"])

            # The roles a signed-in user holds: `public_member` in public, and a
            # project role in each project they are on, their personal one included.
            for user_id in (member, stranger):
                await _grant_image_read(sess, public_node, user_id)
            await _grant_image_read(sess, project_nodes["joined"], member)
            await _grant_image_read(sess, project_nodes["personal"], member)
            await _grant_image_read(sess, project_nodes["other"], stranger)
            await sess.commit()

            return Catalog(
                member=member,
                stranger=stranger,
                images={key: ImageID(row.id) for key, row in rows.items()},
            )

    def _registry_of(self, image_key: str) -> str:
        return "other" if image_key == "personal" else image_key

    async def _public_node(self, sess: AsyncSession) -> VirtualEntityRow:
        return (
            await sess.execute(
                sa.select(VirtualEntityRow)
                .join(GlobalEntityRow, GlobalEntityRow.id == VirtualEntityRow.entity_id)
                .where(GlobalEntityRow.name == GlobalEntityName.PUBLIC)
            )
        ).scalar_one()

    async def _write_accounts(
        self,
        sess: AsyncSession,
        user_ids: Sequence[UserID],
        project_ids: Sequence[ProjectID],
        personal_project: ProjectID,
        personal_owner: UserID,
    ) -> None:
        domain_id = DomainID(uuid.uuid4())
        sess.add(
            DomainRow(
                id=domain_id,
                name=_DOMAIN_NAME,
                description="Visible image scenarios",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
        )
        sess.add(
            UserResourcePolicyRow(
                name=_POLICY_NAME,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        sess.add(
            ProjectResourcePolicyRow(
                name=_POLICY_NAME,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_network_count=10,
            )
        )
        await sess.flush()
        sess.add_all([
            UserRow(
                uuid=user_id,
                username=f"user-{uuid.uuid4().hex[:8]}",
                email=f"{uuid.uuid4().hex[:8]}@test.io",
                domain_name=_DOMAIN_NAME,
                domain_id=domain_id,
                role=UserRole.USER,
                resource_policy=_POLICY_NAME,
            )
            for user_id in user_ids
        ])
        await sess.flush()
        sess.add_all([
            ProjectRow(
                id=project_id,
                name=f"project-{uuid.uuid4().hex[:8]}",
                domain_name=_DOMAIN_NAME,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=_POLICY_NAME,
                type=ProjectType.GENERAL,
            )
            for project_id in project_ids
        ])
        sess.add(
            ProjectRow(
                id=personal_project,
                name=f"personal-{uuid.uuid4().hex[:8]}",
                domain_name=_DOMAIN_NAME,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=_POLICY_NAME,
                type=ProjectType.PERSONAL,
                creator_id=personal_owner,
            )
        )
        await sess.flush()

    async def _visible(
        self, db: ExtendedAsyncSAEngine, scopes: Sequence[OperationScope]
    ) -> set[uuid.UUID]:
        querier = BatchQuerier(
            conditions=[], orders=[], pagination=OffsetPagination(limit=100, offset=0)
        )
        async with db.begin_readonly_session() as sess:
            result = await execute_batch_querier(
                sess, sa.select(ImageRow), querier, scopes=list(scopes)
            )
        return {row.ImageRow.id for row in result.rows}

    async def _read_permissions(
        self, db: ExtendedAsyncSAEngine, user_id: UserID, images: Sequence[ImageID]
    ) -> dict[ImageID, Permission]:
        async with db.begin_readonly_session() as sess:
            granted = await PermissionReadOps(sess).owned_permissions([
                OwnCheckKey(user_id=user_id, entity=image) for image in images
            ])
        return {ImageID(key.entity): bits for key, bits in granted.items()}

    async def test_the_caller_reads_public_their_own_and_their_projects(
        self, image_db: ExtendedAsyncSAEngine, catalog: Catalog
    ) -> None:
        visible = await self._visible(image_db, [VisibleImageTarget(user_id=catalog.member)])

        assert visible == catalog.image_ids("public", "personal", "joined")

    async def test_a_project_the_caller_is_not_on_is_left_out(
        self, image_db: ExtendedAsyncSAEngine, catalog: Catalog
    ) -> None:
        visible = await self._visible(image_db, [VisibleImageTarget(user_id=catalog.member)])

        assert catalog.image_ids("other").isdisjoint(visible)

    async def test_another_caller_reads_their_own_projects_instead(
        self, image_db: ExtendedAsyncSAEngine, catalog: Catalog
    ) -> None:
        visible = await self._visible(image_db, [VisibleImageTarget(user_id=catalog.stranger)])

        assert visible == catalog.image_ids("public", "personal", "other")

    async def test_the_scope_and_the_permission_check_agree(
        self, image_db: ExtendedAsyncSAEngine, catalog: Catalog
    ) -> None:
        """Every image the scope returns is one the check answers READ for, and every
        image it leaves out is one the check refuses."""
        visible = await self._visible(image_db, [VisibleImageTarget(user_id=catalog.member)])
        granted = await self._read_permissions(
            image_db, catalog.member, list(catalog.images.values())
        )

        reads = {image for image, bits in granted.items() if bits & Permission.READ}
        assert {uuid.UUID(str(image)) for image in reads} == visible
