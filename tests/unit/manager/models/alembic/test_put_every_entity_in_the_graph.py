"""Verifies the entity graph backfill migration against a real database.

Static analysis does not reach the migration's SQL, so the data migration is exercised
here: rows written without their graph rows go in, the migration runs, and the graph
rows it wrote are read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Final

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import QuotaScopeID, ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.entity_share.types import EntityShareStatus
from ai.backend.manager.data.vfolder.types import (
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.alembic.versions.dafe06a6c763_put_every_entity_in_the_graph import (
    NODE_SOURCES,
    put_every_entity_in_the_graph,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.base import metadata
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.network.row import NetworkRow
from ai.backend.manager.models.notification.row import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.project.row import AssocGroupUserRow
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_template.row import SessionTemplateRow
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import with_tables

# The rows the migration reads beyond those the scenarios write. Importing them registers
# their tables, which a test sandbox does not do on its own.
_READ_ROWS: Final = (
    AgentRow,
    AppConfigAllowListRow,
    AppConfigDefinitionRow,
    AppConfigFragmentRow,
    ArtifactRow,
    AssociationContainerRegistriesGroupsRow,
    ClientIPMaskingPolicyRow,
    DeploymentRevisionPresetRow,
    EndpointRow,
    HuggingFaceRegistryRow,
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
    ImageRow,
    KeyPairRow,
    LoginClientTypeRow,
    ModelCardRow,
    NetworkRow,
    NotificationChannelRow,
    NotificationRuleRow,
    ObjectStorageRow,
    AssocGroupUserRow,
    PrometheusQueryPresetRow,
    PrometheusQueryPresetCategoryRow,
    PermissionRow,
    ReservoirRegistryRow,
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
    KeyPairResourcePolicyRow,
    ResourcePresetRow,
    ResourceSlotTypeRow,
    RetentionPolicyRow,
    RuntimeVariantRow,
    RuntimeVariantPresetRow,
    ServiceCatalogRow,
    SessionRow,
    SessionGroupRow,
    SessionTemplateRow,
    StorageNamespaceRow,
    EntityMembershipFieldRow,
    VFSStorageRow,
)


def _tables() -> list[Table]:
    """Every table the migration reads, with the tables they reference, parents first."""
    written = (
        DomainRow,
        UserRow,
        ProjectRow,
        VFolderRow,
        ContainerRegistryRow,
        EntityShareRow,
        RoleRow,
        RolePresetRow,
        RolePermissionPresetRow,
        UserRoleRow,
        ProjectResourcePolicyRow,
        UserResourcePolicyRow,
        VirtualEntityRow,
        EntityMembershipRow,
        EntityMembershipCapRow,
        ScopeBindingRow,
    )
    names = {row.__table__.name for row in (*written, *_READ_ROWS)}
    assert names >= {table for _, table, _ in NODE_SOURCES}
    frontier = list(names)
    while frontier:
        table = metadata.tables[frontier.pop()]
        for fk in table.foreign_keys:
            referred = fk.column.table.name
            if referred not in names:
                names.add(referred)
                frontier.append(referred)
    return [table for table in metadata.sorted_tables if table.name in names]


@dataclass
class Fixture:
    domain_id: DomainID
    domain_name: DomainName
    user_id: uuid.UUID
    personal_project_id: uuid.UUID
    team_project_id: uuid.UUID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _tables()):
        yield database_connection


@pytest.fixture
async def fixture(db: ExtendedAsyncSAEngine) -> Fixture:
    """A domain, a user, their personal project and a team project the user is on, with
    no graph rows at all."""
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
        await session.commit()
    async with db.begin() as conn:
        await conn.execute(
            sa.text("INSERT INTO association_groups_users (group_id, user_id) VALUES (:g, :u)"),
            {"g": team_project_id, "u": user_id},
        )
    return Fixture(
        domain_id=domain_id,
        domain_name=domain_name,
        user_id=user_id,
        personal_project_id=personal_project_id,
        team_project_id=team_project_id,
    )


async def _add_vfolder(db: ExtendedAsyncSAEngine, fx: Fixture, project_id: uuid.UUID) -> uuid.UUID:
    vfolder_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            VFolderRow(
                id=vfolder_id,
                name=f"vf-{vfolder_id.hex[:8]}",
                domain_name=fx.domain_name,
                quota_scope_id=QuotaScopeID.parse(f"project:{project_id}"),
                host="local",
                creator="alice@test.local",
                creator_id=fx.user_id,
                ownership_type=VFolderOwnershipType.GROUP,
                user=None,
                group=project_id,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )
        )
        await session.commit()
    return vfolder_id


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(put_every_entity_in_the_graph)


async def _node_of(db: ExtendedAsyncSAEngine, entity_type: str, entity_id: uuid.UUID) -> uuid.UUID:
    async with db.begin_readonly_session() as session:
        node = await session.scalar(
            sa.select(VirtualEntityRow.id).where(
                VirtualEntityRow.entity_type == entity_type,
                VirtualEntityRow.entity_id == entity_id,
            )
        )
    assert node is not None
    return node


async def _edge(
    db: ExtendedAsyncSAEngine, owner: uuid.UUID, member: uuid.UUID
) -> EntityMembershipRow | None:
    async with db.begin_readonly_session() as session:
        edge: EntityMembershipRow | None = await session.scalar(
            sa.select(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id == owner,
                EntityMembershipRow.member_entity_id == member,
            )
        )
        return edge


async def _caps(db: ExtendedAsyncSAEngine, membership_id: uuid.UUID) -> set[int]:
    async with db.begin_readonly_session() as session:
        return {
            int(bit)
            for bit in (
                await session.scalars(
                    sa.select(EntityMembershipCapRow.permission).where(
                        EntityMembershipCapRow.membership_id == membership_id
                    )
                )
            ).all()
        }


async def _binding_cap(
    db: ExtendedAsyncSAEngine, node: uuid.UUID, scope: uuid.UUID
) -> tuple[bool, Permission | None]:
    """Whether the scope governs the node, and under which cap."""
    async with db.begin_readonly_session() as session:
        row = (
            await session.execute(
                sa.select(ScopeBindingRow.permission_cap).where(
                    ScopeBindingRow.virtual_entity_id == node,
                    ScopeBindingRow.scope_entity_id == scope,
                )
            )
        ).first()
    return (row is not None, row[0] if row is not None else None)


class TestPutEveryEntityInTheGraph:
    async def test_every_row_gets_a_node_owning_and_governing_itself(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _run(db)

        for entity_type, entity_id in (
            ("domain", fixture.domain_id),
            ("user", fixture.user_id),
            ("project", fixture.team_project_id),
        ):
            node = await _node_of(db, entity_type, entity_id)
            assert await _edge(db, node, node) is not None
            assert await _binding_cap(db, node, node) == (True, None)

    async def test_a_row_is_owned_and_governed_by_the_scopes_it_was_created_in(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        vfolder_id = await _add_vfolder(db, fixture, fixture.team_project_id)

        await _run(db)

        domain = await _node_of(db, "domain", fixture.domain_id)
        project = await _node_of(db, "project", fixture.team_project_id)
        user = await _node_of(db, "user", fixture.user_id)
        vfolder = await _node_of(db, "vfolder", vfolder_id)
        for scope, node in ((domain, user), (domain, project), (project, vfolder)):
            edge = await _edge(db, scope, node)
            assert edge is not None
            assert edge.capped is False
            assert await _binding_cap(db, node, scope) == (True, None)

    async def test_the_roster_is_a_read_capped_share_without_a_binding(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        async with db.begin_session() as session:
            project = VirtualEntityRow(entity_type="project", entity_id=fixture.team_project_id)
            user = VirtualEntityRow(entity_type="user", entity_id=fixture.user_id)
            session.add_all([project, user])
            await session.flush()
            session.add(
                EntityMembershipRow(
                    virtual_entity_id=project.id, member_entity_id=user.id, capped=False
                )
            )
            session.add(
                ScopeBindingRow(
                    virtual_entity_id=user.id, scope_entity_id=project.id, permission_cap=None
                )
            )
            await session.commit()
            project_node, user_node = project.id, user.id

        await _run(db)

        personal_node = await _node_of(db, "project", fixture.personal_project_id)
        for scope in (project_node, personal_node):
            edge = await _edge(db, scope, user_node)
            assert edge is not None
            assert edge.capped is True
            assert await _caps(db, edge.id) == {int(Permission.READ)}
            assert (await _binding_cap(db, user_node, scope))[0] is False

    async def test_a_relation_is_governed_and_shared_under_read(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        registry_id = ContainerRegistryID(uuid.uuid4())
        async with db.begin_session() as session:
            session.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url="https://docker.io",
                    registry_name=f"reg-{uuid.uuid4().hex[:8]}",
                    type=ContainerRegistryType.DOCKER,
                )
            )
            await session.commit()
        async with db.begin() as conn:
            await conn.execute(
                sa.text(
                    "INSERT INTO association_container_registries_groups (registry_id, group_id)"
                    " VALUES (:r, :g)"
                ),
                {"r": registry_id, "g": fixture.team_project_id},
            )

        await _run(db)

        registry = await _node_of(db, "container_registry", registry_id)
        project = await _node_of(db, "project", fixture.team_project_id)
        assert await _binding_cap(db, registry, project) == (True, Permission.READ)
        edge = await _edge(db, registry, project)
        assert edge is not None
        assert edge.capped is True
        assert await _caps(db, edge.id) == {int(Permission.READ)}

    async def test_an_accepted_share_to_a_user_lands_in_their_personal_project(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        vfolder_id = await _add_vfolder(db, fixture, fixture.team_project_id)
        async with db.begin_session() as session:
            # A share names its target and recipient by their nodes.
            session.add(VirtualEntityRow(entity_type="vfolder", entity_id=vfolder_id))
            session.add(VirtualEntityRow(entity_type="user", entity_id=fixture.user_id))
            await session.flush()
            session.add(
                EntityShareRow(
                    sharer_user_id=None,
                    recipient_entity_type=UserEntityType(),
                    recipient_entity_id=fixture.user_id,
                    target_entity_type=VFolderEntityType(),
                    target_entity_id=vfolder_id,
                    permission_cap=Permission.READ | Permission.UPDATE,
                    status=EntityShareStatus.ACCEPTED,
                )
            )
            await session.commit()

        await _run(db)

        personal = await _node_of(db, "project", fixture.personal_project_id)
        vfolder = await _node_of(db, "vfolder", vfolder_id)
        edge = await _edge(db, personal, vfolder)
        assert edge is not None
        assert edge.capped is True
        assert await _caps(db, edge.id) == {int(Permission.READ), int(Permission.UPDATE)}

    async def test_a_scope_without_its_preset_roles_gets_them_and_their_grants(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        async with db.begin_session() as session:
            preset = RolePresetRow(name="project_member", scope_type="project", auto_assign=True)
            session.add(preset)
            await session.flush()
            session.add(
                RolePermissionPresetRow(
                    role_preset_id=preset.id,
                    entity_type=VFolderEntityType(),
                    permission=Permission.READ,
                )
            )
            await session.commit()
            preset_id = preset.id

        await _run(db)

        async with db.begin_readonly_session() as session:
            role = await session.scalar(
                sa.select(RoleRow).where(
                    RoleRow.role_preset_id == preset_id,
                    RoleRow.scope_id == fixture.personal_project_id,
                )
            )
            assert role is not None
            granted = await session.scalar(
                sa.select(UserRoleRow.id).where(
                    UserRoleRow.user_id == fixture.user_id, UserRoleRow.role_id == role.id
                )
            )
        assert granted is not None
        role_node = await _node_of(db, "role", role.id)
        project = await _node_of(db, "project", fixture.personal_project_id)
        assert await _binding_cap(db, role_node, project) == (True, None)

    async def test_running_twice_changes_nothing(
        self, db: ExtendedAsyncSAEngine, fixture: Fixture
    ) -> None:
        await _add_vfolder(db, fixture, fixture.team_project_id)

        await _run(db)
        async with db.begin_readonly_session() as session:
            counts = [
                await session.scalar(sa.select(sa.func.count()).select_from(table))
                for table in (VirtualEntityRow, EntityMembershipRow, ScopeBindingRow, RoleRow)
            ]
        await _run(db)
        async with db.begin_readonly_session() as session:
            again = [
                await session.scalar(sa.select(sa.func.count()).select_from(table))
                for table in (VirtualEntityRow, EntityMembershipRow, ScopeBindingRow, RoleRow)
            ]

        assert again == counts
