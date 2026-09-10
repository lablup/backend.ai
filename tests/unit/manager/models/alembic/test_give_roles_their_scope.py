"""Verifies the role scope backfill migration against a real database.

Static analysis does not reach the migration's SQL, so the backfill is exercised here:
roles holding permissions go in, the backfill runs, and the scope columns and the
graph are read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import Permission, RoleSource
from ai.backend.manager.data.permission.types import ScopeType as LegacyScopeType
from ai.backend.manager.models.alembic.versions.a7d2c9e41b58_give_roles_their_scope import (
    backfill,
)
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.rbac_models.permission.object_permission import (
    ObjectPermissionRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

# The permission rows carried a scope when this migration ran; the column is gone from
# the model since, so the pre-migration shape is declared here.
_metadata = sa.MetaData()
_permissions = sa.Table(
    "permissions",
    _metadata,
    sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
    sa.Column("role_id", GUID, nullable=False),
    sa.Column("scope_type", sa.String(32), nullable=False),
    sa.Column("scope_id", sa.String(64), nullable=False),
    sa.Column("entity_type", sa.String(32), nullable=False),
    sa.Column("permission", sa.Integer, nullable=False),
    sa.Column("all_fields", sa.Boolean, nullable=False, server_default=sa.true()),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
)

# The migration clears the association rows of the roles it drops; the table is gone
# from the models since, so its pre-migration shape is declared here too.
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
    RolePresetRow,
    RoleRow,
    _permissions,
    _association_scopes_entities,
    ObjectPermissionRow,
    VirtualEntityRow,
    EntityMembershipRow,
    ScopeBindingRow,
]

_PROJECT = EntityType("project")
_ROLE = EntityType("role")


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


async def _add_scope(db: ExtendedAsyncSAEngine) -> uuid.UUID:
    scope_id = uuid.uuid4()
    async with db.begin_session() as session:
        node = VirtualEntityRow(entity_type=_PROJECT, entity_id=scope_id)
        session.add(node)
        await session.flush()
        session.add(EntityMembershipRow(virtual_entity_id=node.id, member_entity_id=node.id))
    return scope_id


async def _add_preset(db: ExtendedAsyncSAEngine) -> uuid.UUID:
    async with db.begin_session() as session:
        preset = RolePresetRow(name="member", scope_type=LegacyScopeType.PROJECT)
        session.add(preset)
        await session.flush()
        return preset.id


async def _add_role(
    db: ExtendedAsyncSAEngine,
    *,
    permissions_in: Sequence[uuid.UUID] = (),
    enrolled_in: Sequence[uuid.UUID] = (),
    preset_id: uuid.UUID | None = None,
    with_node: bool = True,
) -> uuid.UUID:
    """A role holding one permission per entry of ``permissions_in`` (a scope may
    repeat), enrolled in ``enrolled_in`` through the graph. The row's scope columns
    hold a placeholder scope, as a row from before the migration would not."""
    role_id = uuid.uuid4()
    placeholder = await _add_scope(db)
    async with db.begin_session() as session:
        session.add(
            RoleRow(
                id=role_id,
                name=f"role-{role_id.hex[:8]}",
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                role_preset_id=preset_id,
                scope_type=_PROJECT,
                scope_id=placeholder,
            )
        )
        await session.flush()
        if with_node:
            role_node = VirtualEntityRow(entity_type=_ROLE, entity_id=role_id)
            session.add(role_node)
            await session.flush()
            session.add(
                EntityMembershipRow(virtual_entity_id=role_node.id, member_entity_id=role_node.id)
            )
            for scope_id in enrolled_in:
                scope_node_id = await session.scalar(
                    sa.select(VirtualEntityRow.id).where(VirtualEntityRow.entity_id == scope_id)
                )
                session.add(
                    EntityMembershipRow(
                        virtual_entity_id=scope_node_id, member_entity_id=role_node.id
                    )
                )
        for index, scope_id in enumerate(permissions_in):
            await session.execute(
                sa.insert(_permissions).values(
                    role_id=role_id,
                    scope_type=_PROJECT,
                    scope_id=str(scope_id),
                    entity_type=EntityType(f"entity-{index}"),
                    permission=int(Permission.READ),
                )
            )
    return role_id


async def _run_backfill(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(backfill)


async def _scopes(db: ExtendedAsyncSAEngine) -> dict[uuid.UUID, tuple[str, uuid.UUID]]:
    async with db.begin_readonly_session() as session:
        rows = (
            await session.execute(sa.select(RoleRow.id, RoleRow.scope_type, RoleRow.scope_id))
        ).all()
        return {row.id: (row.scope_type, row.scope_id) for row in rows}


async def _owners(db: ExtendedAsyncSAEngine, role_id: uuid.UUID) -> set[uuid.UUID]:
    """The entity ids of the nodes owning the role's node, its own included."""
    role_node = (
        sa.select(VirtualEntityRow.id)
        .where(VirtualEntityRow.entity_type == _ROLE, VirtualEntityRow.entity_id == role_id)
        .scalar_subquery()
    )
    async with db.begin_readonly_session() as session:
        rows = await session.scalars(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.virtual_entity_id == VirtualEntityRow.id)
            .where(EntityMembershipRow.member_entity_id == role_node)
        )
        return set(rows.all())


class TestRoleScopeBackfill:
    async def test_a_role_takes_the_scope_most_of_its_permissions_name(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        first = await _add_scope(db)
        second = await _add_scope(db)
        role_id = await _add_role(db, permissions_in=[first, second, second])

        await _run_backfill(db)

        assert (await _scopes(db))[role_id] == (_PROJECT, second)

    async def test_a_role_without_permissions_is_removed(self, db: ExtendedAsyncSAEngine) -> None:
        role_id = await _add_role(db, enrolled_in=[await _add_scope(db)])

        await _run_backfill(db)

        assert role_id not in await _scopes(db)
        assert await _owners(db, role_id) == set()

    async def test_a_role_whose_scope_has_no_node_is_removed(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        role_id = await _add_role(db, permissions_in=[uuid.uuid4()])

        await _run_backfill(db)

        assert role_id not in await _scopes(db)

    async def test_the_graph_follows_the_column(self, db: ExtendedAsyncSAEngine) -> None:
        permitted = await _add_scope(db)
        enrolled = await _add_scope(db)
        role_id = await _add_role(db, permissions_in=[permitted], enrolled_in=[enrolled])

        await _run_backfill(db)

        assert (await _scopes(db))[role_id] == (_PROJECT, permitted)
        assert await _owners(db, role_id) == {role_id, permitted}

    async def test_a_role_without_a_node_gets_one(self, db: ExtendedAsyncSAEngine) -> None:
        project_id = await _add_scope(db)
        role_id = await _add_role(db, permissions_in=[project_id], with_node=False)

        await _run_backfill(db)

        assert await _owners(db, role_id) == {role_id, project_id}

    async def test_two_roles_of_one_preset_in_one_scope_stop_the_migration(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        project_id = await _add_scope(db)
        preset_id = await _add_preset(db)
        first = await _add_role(db, permissions_in=[project_id], preset_id=preset_id)
        await _add_role(db, permissions_in=[project_id], preset_id=preset_id)

        with pytest.raises(RuntimeError, match=str(first)):
            await _run_backfill(db)

    async def test_running_it_again_keeps_the_scopes(self, db: ExtendedAsyncSAEngine) -> None:
        project_id = await _add_scope(db)
        role_id = await _add_role(db, permissions_in=[project_id])

        await _run_backfill(db)
        await _run_backfill(db)

        assert (await _scopes(db))[role_id] == (_PROJECT, project_id)
        assert await _owners(db, role_id) == {role_id, project_id}
