"""Verifies the role -> preset backfill migration against a real database.

Static analysis does not reach the migration's SQL, so the backfill is exercised here:
presets and scope-bound roles go in, the backfill runs, and the links are read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import EntityType as LegacyEntityType
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.data.permission.types import ScopeType as LegacyScopeType
from ai.backend.manager.models.alembic.versions.b8c828d3636e_link_roles_to_their_preset import (
    backfill,
)
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

# The migration reads the association rows the roles were bound through; the table is
# gone from the models since, so its pre-migration shape is declared here.
_metadata = sa.MetaData()
_association_scopes_entities = sa.Table(
    "association_scopes_entities",
    _metadata,
    sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
    sa.Column("scope_type", sa.String(32), nullable=False),
    sa.Column("scope_id", sa.String(64), nullable=False),
    sa.Column("entity_type", sa.String(32), nullable=False),
    sa.Column("entity_id", sa.String(64), nullable=False),
)

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    RolePresetRow,
    RoleRow,
    VirtualEntityRow,
    EntityMembershipRow,
    _association_scopes_entities,
]


@dataclass
class DomainFixture:
    name: DomainName
    id: DomainID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def domain(db: ExtendedAsyncSAEngine) -> DomainFixture:
    domain_id = DomainID(uuid.uuid4())
    domain_name = DomainName(f"test-domain-{uuid.uuid4().hex[:8]}")
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
    return DomainFixture(name=domain_name, id=domain_id)


async def _add_preset(
    db: ExtendedAsyncSAEngine,
    name: str,
    *,
    template: str | None = None,
    scope_type: LegacyScopeType = LegacyScopeType.PROJECT,
    deleted: bool = False,
) -> uuid.UUID:
    async with db.begin_session() as session:
        preset = RolePresetRow(
            name=name, role_name_template=template, scope_type=scope_type, deleted=deleted
        )
        session.add(preset)
        await session.flush()
        return preset.id


async def _add_project(db: ExtendedAsyncSAEngine, domain: DomainFixture, name: str) -> uuid.UUID:
    project_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            ProjectRow(
                id=project_id,
                name=name,
                domain_name=domain.name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                resource_policy="default",
                type=ProjectType.GENERAL,
            )
        )
        session.add(VirtualEntityRow(entity_type="project", entity_id=project_id))
    return project_id


async def _add_role(
    db: ExtendedAsyncSAEngine,
    name: str,
    project_id: uuid.UUID,
    *,
    source: RoleSource = RoleSource.SYSTEM,
    via_graph: bool = False,
) -> uuid.UUID:
    """A role bound to the project as the legacy association writes it, or through the
    virtual entity graph when ``via_graph``."""
    role_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            RoleRow(
                id=role_id,
                name=name,
                source=source,
                status=RoleStatus.ACTIVE,
                scope_type="project",
                scope_id=project_id,
            )
        )
        if via_graph:
            scope_node_id = await session.scalar(
                sa.select(VirtualEntityRow.id).where(VirtualEntityRow.entity_id == project_id)
            )
            role_node = VirtualEntityRow(entity_type="role", entity_id=role_id)
            session.add(role_node)
            await session.flush()
            session.add(
                EntityMembershipRow(
                    virtual_entity_id=scope_node_id, member_entity_id=role_node.id, capped=False
                )
            )
        else:
            await session.execute(
                sa.insert(_association_scopes_entities).values(
                    scope_type=LegacyScopeType.PROJECT.value,
                    scope_id=str(project_id),
                    entity_type=LegacyEntityType.ROLE.value,
                    entity_id=str(role_id),
                )
            )
    return role_id


async def _run_backfill(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(backfill)


async def _links(db: ExtendedAsyncSAEngine) -> dict[uuid.UUID, uuid.UUID | None]:
    async with db.begin_readonly_session() as session:
        rows = (await session.execute(sa.select(RoleRow.id, RoleRow.role_preset_id))).all()
        return {row.id: row.role_preset_id for row in rows}


class TestRolePresetLinkBackfill:
    async def test_legacy_name_links_through_the_association(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        preset_id = await _add_preset(db, "member")
        project_id = await _add_project(db, domain, "alpha")
        role_id = await _add_role(db, "member", project_id)

        await _run_backfill(db)

        assert (await _links(db))[role_id] == preset_id

    async def test_generated_name_links_through_the_graph(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        preset_id = await _add_preset(db, "member")
        project_id = await _add_project(db, domain, "alpha")
        role_id = await _add_role(db, f"member-{str(project_id)[:8]}", project_id, via_graph=True)

        await _run_backfill(db)

        assert (await _links(db))[role_id] == preset_id

    async def test_templated_name_is_rendered_from_the_scope(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        preset_id = await _add_preset(db, "member", template="{{ scope.name }}-member")
        project_id = await _add_project(db, domain, "alpha")
        role_id = await _add_role(db, "alpha-member", project_id)

        await _run_backfill(db)

        assert (await _links(db))[role_id] == preset_id

    async def test_other_names_stay_unlinked(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        await _add_preset(db, "member", template="{{ scope.name }}-member")
        project_id = await _add_project(db, domain, "alpha")
        mismatch = await _add_role(db, "beta-member", project_id)
        fallback = await _add_role(db, f"project-{str(project_id)[:8]}-role", project_id)
        custom = await _add_role(db, "member", project_id, source=RoleSource.CUSTOM)

        await _run_backfill(db)

        links = await _links(db)
        assert links[mismatch] is None
        assert links[fallback] is None
        assert links[custom] is None

    async def test_a_name_two_presets_yield_is_left_alone(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        await _add_preset(db, "member")
        await _add_preset(db, "other", template="member")
        project_id = await _add_project(db, domain, "alpha")
        role_id = await _add_role(db, "member", project_id)

        await _run_backfill(db)

        assert (await _links(db))[role_id] is None

    async def test_a_deleted_preset_and_another_scope_type_do_not_link(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        await _add_preset(db, "member", deleted=True)
        await _add_preset(db, "viewer", scope_type=LegacyScopeType.DOMAIN)
        project_id = await _add_project(db, domain, "alpha")
        deleted = await _add_role(db, "member", project_id)
        other_type = await _add_role(db, "viewer", project_id)

        await _run_backfill(db)

        links = await _links(db)
        assert links[deleted] is None
        assert links[other_type] is None

    async def test_running_it_again_keeps_the_links(
        self, db: ExtendedAsyncSAEngine, domain: DomainFixture
    ) -> None:
        preset_id = await _add_preset(db, "member")
        project_id = await _add_project(db, domain, "alpha")
        role_id = await _add_role(db, "member", project_id)

        await _run_backfill(db)
        await _run_backfill(db)

        assert (await _links(db))[role_id] == preset_id
