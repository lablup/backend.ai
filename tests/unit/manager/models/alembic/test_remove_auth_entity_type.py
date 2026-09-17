"""Verifies the auth entity type removal migration against a real database.

Static analysis does not reach the migration's SQL, so the deletion is exercised here:
permission and preset permission rows naming `auth` and another type go in, the
migration runs, and what is left is read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import Permission, RoleSource
from ai.backend.manager.models.alembic.versions.b3e7a1f09c42_remove_the_auth_entity_type_from_permissions import (
    remove_retired_permissions,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    RolePresetRow,
    RolePermissionPresetRow,
    RoleRow,
    PermissionRow,
]

_AUTH = EntityType("auth")
_USER = EntityType("user")


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def preset_id(db: ExtendedAsyncSAEngine) -> uuid.UUID:
    async with db.begin_session() as session:
        preset = RolePresetRow(name="member", scope_type=_USER)
        session.add(preset)
        await session.flush()
        for entity_type in (_AUTH, _USER):
            session.add(
                RolePermissionPresetRow(
                    role_preset_id=preset.id, entity_type=entity_type, permission=Permission.READ
                )
            )
        return preset.id


@pytest.fixture
async def role_id(db: ExtendedAsyncSAEngine) -> uuid.UUID:
    role_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(
            RoleRow(
                id=role_id,
                name=f"role-{role_id.hex[:8]}",
                source=RoleSource.CUSTOM,
                status=RoleStatus.ACTIVE,
                scope_type=_USER,
                scope_id=uuid.uuid4(),
            )
        )
        await session.flush()
        for entity_type in (_AUTH, _USER):
            session.add(
                PermissionRow(role_id=role_id, entity_type=entity_type, permission=Permission.READ)
            )
    return role_id


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(remove_retired_permissions)


async def _permission_types(db: ExtendedAsyncSAEngine, role_id: uuid.UUID) -> set[str]:
    async with db.begin_readonly_session() as session:
        rows = await session.scalars(
            sa.select(PermissionRow.entity_type).where(PermissionRow.role_id == role_id)
        )
        return set(rows.all())


async def _preset_types(db: ExtendedAsyncSAEngine, preset_id: uuid.UUID) -> set[str]:
    async with db.begin_readonly_session() as session:
        rows = await session.scalars(
            sa.select(RolePermissionPresetRow.entity_type).where(
                RolePermissionPresetRow.role_preset_id == preset_id
            )
        )
        return set(rows.all())


class TestRemoveAuthEntityType:
    async def test_only_the_auth_rows_are_removed(
        self, db: ExtendedAsyncSAEngine, role_id: uuid.UUID, preset_id: uuid.UUID
    ) -> None:
        await _run(db)

        assert await _permission_types(db, role_id) == {_USER}
        assert await _preset_types(db, preset_id) == {_USER}

    async def test_running_it_again_keeps_the_rest(
        self, db: ExtendedAsyncSAEngine, role_id: uuid.UUID, preset_id: uuid.UUID
    ) -> None:
        await _run(db)
        await _run(db)

        assert await _permission_types(db, role_id) == {_USER}
        assert await _preset_types(db, preset_id) == {_USER}
