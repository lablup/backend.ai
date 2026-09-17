"""Runs the permission-scope drop's pre-checks against a real database.

A folder share granted the invitee's role a row scoped to the folder. Those rows are
dropped before the check that stops on rows disagreeing with their role's scope.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.alembic.versions.c092d242a027_drop_the_scope_from_permission_rows import (
    drop_folder_share_grants,
    refuse_rows_disagreeing_with_their_role,
)
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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

_TABLES: list[Table | type[HasTable]] = [
    VirtualEntityRow,
    RolePresetRow,
    RoleRow,
    _permissions,
]

_USER = EntityType("user")


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def user_role(db: ExtendedAsyncSAEngine) -> tuple[uuid.UUID, uuid.UUID]:
    """A user's role sitting in the user's scope, answered as (role id, user id)."""
    role_id = uuid.uuid4()
    user_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(VirtualEntityRow(entity_type=_USER, entity_id=user_id))
        await session.flush()
        session.add(
            RoleRow(
                id=role_id,
                name=f"role_user_{user_id.hex[:8]}",
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                scope_type=_USER,
                scope_id=user_id,
            )
        )
    return role_id, user_id


async def _grant(
    db: ExtendedAsyncSAEngine, role_id: uuid.UUID, scope_type: str, scope_id: uuid.UUID
) -> None:
    async with db.begin() as conn:
        await conn.execute(
            sa.insert(_permissions).values(
                role_id=role_id,
                scope_type=scope_type,
                scope_id=str(scope_id),
                entity_type="vfolder",
                permission=1,
            )
        )


async def _scopes(db: ExtendedAsyncSAEngine, role_id: uuid.UUID) -> set[tuple[str, str]]:
    async with db.begin_readonly_session() as session:
        rows = await session.execute(
            sa.select(_permissions.c.scope_type, _permissions.c.scope_id).where(
                _permissions.c.role_id == role_id
            )
        )
        return {(row.scope_type, row.scope_id) for row in rows}


async def _drop_and_check(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(drop_folder_share_grants)
        await conn.run_sync(refuse_rows_disagreeing_with_their_role)


class TestDropFolderShareGrants:
    async def test_a_share_grant_goes_and_the_check_passes(
        self, db: ExtendedAsyncSAEngine, user_role: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        role_id, user_id = user_role
        folder_id = uuid.uuid4()
        await _grant(db, role_id, "user", user_id)
        await _grant(db, role_id, "vfolder", folder_id)

        await _drop_and_check(db)

        assert await _scopes(db, role_id) == {("user", str(user_id))}

    async def test_another_disagreeing_row_still_stops_the_migration(
        self, db: ExtendedAsyncSAEngine, user_role: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        role_id, _ = user_role
        await _grant(db, role_id, "project", uuid.uuid4())

        with pytest.raises(RuntimeError):
            await _drop_and_check(db)
