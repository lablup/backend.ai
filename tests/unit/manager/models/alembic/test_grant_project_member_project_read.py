"""Runs the project_member project READ grant against a real database and reads the rows back."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.permission.types import Permission, RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.alembic.versions.a0f597deb5e5_grant_project_members_read_on_their_project import (
    _PRESET_ID,
    grant,
    revoke,
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

_PRESET_UUID = uuid.UUID(_PRESET_ID)
_PROJECT = "project"
_PROJECT_READ = (_PROJECT, Permission.READ)
_SESSION_CREATE = ("session", Permission.CREATE)


@dataclass
class _Fixture:
    plain_role: uuid.UUID
    role_already_reading: uuid.UUID
    other_preset_role: uuid.UUID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


def _role(role_id: uuid.UUID, preset_id: uuid.UUID) -> RoleRow:
    return RoleRow(
        id=role_id,
        name=f"role-{str(role_id)[:8]}",
        source=RoleSource.SYSTEM,
        status=RoleStatus.ACTIVE,
        auto_assign=True,
        role_preset_id=preset_id,
        scope_type=_PROJECT,
        scope_id=uuid.uuid4(),
    )


@pytest.fixture
async def seeded(db: ExtendedAsyncSAEngine) -> _Fixture:
    """Two project_member roles, one already granted project READ, and a role of
    another project preset."""
    other_preset = uuid.uuid4()
    plain_role, role_already_reading, other_preset_role = (uuid.uuid4() for _ in range(3))
    async with db.begin_session() as session:
        for preset_id, name in ((_PRESET_UUID, "project_member"), (other_preset, "other")):
            session.add(
                RolePresetRow(
                    id=preset_id, name=name, scope_type=_PROJECT, auto_assign=True, deleted=False
                )
            )
        await session.flush()
        session.add(
            RolePermissionPresetRow(
                role_preset_id=_PRESET_UUID, entity_type="session", permission=Permission.CREATE
            )
        )
        session.add(_role(plain_role, _PRESET_UUID))
        session.add(_role(role_already_reading, _PRESET_UUID))
        session.add(_role(other_preset_role, other_preset))
        await session.flush()
        for role_id, (entity_type, permission) in (
            (plain_role, _SESSION_CREATE),
            (role_already_reading, _PROJECT_READ),
        ):
            session.add(
                PermissionRow(role_id=role_id, entity_type=entity_type, permission=permission)
            )
        await session.commit()
    return _Fixture(
        plain_role=plain_role,
        role_already_reading=role_already_reading,
        other_preset_role=other_preset_role,
    )


async def _run(db: ExtendedAsyncSAEngine, step: Callable[[sa.engine.Connection], None]) -> None:
    async with db.begin() as conn:
        await conn.run_sync(step)


async def _preset_grants(db: ExtendedAsyncSAEngine) -> set[tuple[str, Permission]]:
    async with db.begin_readonly_session() as session:
        rows = (
            await session.execute(
                sa.select(
                    RolePermissionPresetRow.entity_type, RolePermissionPresetRow.permission
                ).where(RolePermissionPresetRow.role_preset_id == _PRESET_UUID)
            )
        ).all()
    return {(str(entity_type), permission) for entity_type, permission in rows}


async def _grants(db: ExtendedAsyncSAEngine, role_id: uuid.UUID) -> set[tuple[str, Permission]]:
    async with db.begin_readonly_session() as session:
        rows = (
            await session.execute(
                sa.select(PermissionRow.entity_type, PermissionRow.permission).where(
                    PermissionRow.role_id == role_id
                )
            )
        ).all()
    return {(str(entity_type), permission) for entity_type, permission in rows}


class TestGrantProjectMemberProjectRead:
    async def test_the_preset_gains_project_read(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run(db, grant)

        assert await _preset_grants(db) == {_SESSION_CREATE, _PROJECT_READ}

    async def test_every_role_of_the_preset_gains_project_read(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run(db, grant)

        assert await _grants(db, seeded.plain_role) == {_SESSION_CREATE, _PROJECT_READ}
        assert await _grants(db, seeded.role_already_reading) == {_PROJECT_READ}

    async def test_a_role_of_another_preset_is_left_alone(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run(db, grant)

        assert await _grants(db, seeded.other_preset_role) == set()

    async def test_running_again_changes_nothing(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run(db, grant)
        async with db.begin_readonly_session() as session:
            before = [
                await session.scalar(sa.select(sa.func.count()).select_from(table))
                for table in (RolePermissionPresetRow, PermissionRow)
            ]

        await _run(db, grant)

        async with db.begin_readonly_session() as session:
            after = [
                await session.scalar(sa.select(sa.func.count()).select_from(table))
                for table in (RolePermissionPresetRow, PermissionRow)
            ]
        assert after == before

    async def test_downgrade_takes_the_grant_back(
        self, db: ExtendedAsyncSAEngine, seeded: _Fixture
    ) -> None:
        await _run(db, grant)

        await _run(db, revoke)

        assert await _preset_grants(db) == {_SESSION_CREATE}
        assert await _grants(db, seeded.plain_role) == {_SESSION_CREATE}
        assert await _grants(db, seeded.role_already_reading) == set()
