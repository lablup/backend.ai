"""Runs the permission-scope drop's pre-checks against a real database.

A folder share granted the invitee's role a row scoped to the folder, and the session app
service migration granted a session's creator and its project's admins a row scoped to the
session. Those rows are dropped before the check that stops on rows disagreeing with their
role's scope, and so are the rows of a system role ``f4a1c9d20b73`` rewrites or removes and
the rows naming a user, project or domain that no longer exists.
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
    drop_grants_on_deleted_scopes,
    drop_rewritten_system_role_grants,
    drop_session_app_service_grants,
    refuse_rows_disagreeing_with_their_role,
)
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.rbac_models.role.row import RoleRow
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
# The scope tables the cleanup looks a scope up in; only their keys are read.
_users = sa.Table("users", _metadata, sa.Column("uuid", GUID, primary_key=True))
_groups = sa.Table("groups", _metadata, sa.Column("id", GUID, primary_key=True))
_domains = sa.Table("domains", _metadata, sa.Column("id", GUID, primary_key=True))

_TABLES: list[Table | type[HasTable]] = [
    VirtualEntityRow,
    RolePresetRow,
    RoleRow,
    _permissions,
    _users,
    _groups,
    _domains,
]

_USER = EntityType("user")
# A preset ``f4a1c9d20b73`` writes: user_owner.
_REWRITTEN_PRESET = uuid.UUID("776c1366-dcf3-5abd-b8de-bc3ad3b759ad")


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


async def _role_in_user_scope(
    db: ExtendedAsyncSAEngine, source: RoleSource, preset_id: uuid.UUID | None = None
) -> tuple[uuid.UUID, uuid.UUID]:
    role_id = uuid.uuid4()
    user_id = uuid.uuid4()
    async with db.begin_session() as session:
        session.add(VirtualEntityRow(entity_type=_USER, entity_id=user_id))
        if preset_id is not None:
            session.add(
                RolePresetRow(id=preset_id, name=f"preset-{preset_id.hex[:8]}", scope_type=_USER)
            )
        await session.flush()
        session.add(
            RoleRow(
                id=role_id,
                name=f"role_user_{user_id.hex[:8]}",
                source=source,
                status=RoleStatus.ACTIVE,
                scope_type=_USER,
                scope_id=user_id,
                role_preset_id=preset_id,
            )
        )
    async with db.begin() as conn:
        await conn.execute(sa.insert(_users).values(uuid=user_id))
    return role_id, user_id


@pytest.fixture
async def user_role(db: ExtendedAsyncSAEngine) -> tuple[uuid.UUID, uuid.UUID]:
    """A user's system role sitting in the user's scope, answered as (role id, user id)."""
    return await _role_in_user_scope(db, RoleSource.SYSTEM)


@pytest.fixture
async def custom_role(db: ExtendedAsyncSAEngine) -> tuple[uuid.UUID, uuid.UUID]:
    """A custom role sitting in a user's scope, answered as (role id, user id)."""
    return await _role_in_user_scope(db, RoleSource.CUSTOM)


@pytest.fixture
async def live_project(db: ExtendedAsyncSAEngine) -> uuid.UUID:
    project_id = uuid.uuid4()
    async with db.begin() as conn:
        await conn.execute(sa.insert(_groups).values(id=project_id))
    return project_id


async def _grant(
    db: ExtendedAsyncSAEngine,
    role_id: uuid.UUID,
    scope_type: str,
    scope_id: uuid.UUID | str,
    entity_type: str,
) -> None:
    async with db.begin() as conn:
        await conn.execute(
            sa.insert(_permissions).values(
                role_id=role_id,
                scope_type=scope_type,
                scope_id=str(scope_id),
                entity_type=entity_type,
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
        await conn.run_sync(drop_session_app_service_grants)
        await conn.run_sync(drop_rewritten_system_role_grants)
        await conn.run_sync(drop_grants_on_deleted_scopes)
        await conn.run_sync(refuse_rows_disagreeing_with_their_role)


class TestDropFolderShareGrants:
    async def test_a_share_grant_goes_and_the_check_passes(
        self, db: ExtendedAsyncSAEngine, user_role: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        role_id, user_id = user_role
        folder_id = uuid.uuid4()
        await _grant(db, role_id, "user", user_id, entity_type="vfolder")
        await _grant(db, role_id, "vfolder", folder_id, entity_type="vfolder")

        await _drop_and_check(db)

        assert await _scopes(db, role_id) == {("user", str(user_id))}

    async def test_another_disagreeing_row_still_stops_the_migration(
        self,
        db: ExtendedAsyncSAEngine,
        custom_role: tuple[uuid.UUID, uuid.UUID],
        live_project: uuid.UUID,
    ) -> None:
        role_id, _ = custom_role
        await _grant(db, role_id, "project", live_project, entity_type="vfolder")

        with pytest.raises(RuntimeError):
            await _drop_and_check(db)


class TestDropSessionAppServiceGrants:
    async def test_a_session_grant_goes_and_the_check_passes(
        self, db: ExtendedAsyncSAEngine, user_role: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        role_id, user_id = user_role
        session_id = uuid.uuid4()
        await _grant(db, role_id, "user", user_id, entity_type="vfolder")
        await _grant(db, role_id, "session", session_id, entity_type="session:app_service")

        await _drop_and_check(db)

        assert await _scopes(db, role_id) == {("user", str(user_id))}

    async def test_a_grant_in_the_role_s_own_scope_stays(
        self, db: ExtendedAsyncSAEngine, user_role: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        role_id, user_id = user_role
        await _grant(db, role_id, "user", user_id, entity_type="session:app_service")

        await _drop_and_check(db)

        assert await _scopes(db, role_id) == {("user", str(user_id))}


class TestDropRewrittenSystemRoleGrants:
    async def test_a_system_role_without_a_preset_loses_its_other_scope_rows(
        self,
        db: ExtendedAsyncSAEngine,
        user_role: tuple[uuid.UUID, uuid.UUID],
        live_project: uuid.UUID,
    ) -> None:
        role_id, user_id = user_role
        await _grant(db, role_id, "user", user_id, entity_type="vfolder")
        await _grant(db, role_id, "project", live_project, entity_type="vfolder")

        await _drop_and_check(db)

        assert await _scopes(db, role_id) == {("user", str(user_id))}

    async def test_a_system_role_of_a_rewritten_preset_loses_its_other_scope_rows(
        self, db: ExtendedAsyncSAEngine, live_project: uuid.UUID
    ) -> None:
        role_id, user_id = await _role_in_user_scope(db, RoleSource.SYSTEM, _REWRITTEN_PRESET)
        await _grant(db, role_id, "project", live_project, entity_type="vfolder")

        await _drop_and_check(db)

        assert await _scopes(db, role_id) == set()

    async def test_a_system_role_of_another_preset_still_stops_the_migration(
        self, db: ExtendedAsyncSAEngine, live_project: uuid.UUID
    ) -> None:
        role_id, _ = await _role_in_user_scope(db, RoleSource.SYSTEM, uuid.uuid4())
        await _grant(db, role_id, "project", live_project, entity_type="vfolder")

        with pytest.raises(RuntimeError):
            await _drop_and_check(db)


class TestDropGrantsOnDeletedScopes:
    async def test_a_row_naming_a_deleted_project_goes(
        self, db: ExtendedAsyncSAEngine, custom_role: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        role_id, user_id = custom_role
        await _grant(db, role_id, "user", user_id, entity_type="vfolder")
        await _grant(db, role_id, "project", uuid.uuid4(), entity_type="vfolder")

        await _drop_and_check(db)

        assert await _scopes(db, role_id) == {("user", str(user_id))}

    async def test_a_row_naming_a_scope_by_a_non_uuid_goes(
        self, db: ExtendedAsyncSAEngine, custom_role: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        role_id, _ = custom_role
        await _grant(db, role_id, "domain", "default", entity_type="vfolder")

        await _drop_and_check(db)

        assert await _scopes(db, role_id) == set()

    async def test_a_row_naming_a_live_project_stays(
        self,
        db: ExtendedAsyncSAEngine,
        custom_role: tuple[uuid.UUID, uuid.UUID],
        live_project: uuid.UUID,
    ) -> None:
        role_id, _ = custom_role
        await _grant(db, role_id, "project", live_project, entity_type="vfolder")

        async with db.begin() as conn:
            await conn.run_sync(drop_grants_on_deleted_scopes)

        assert await _scopes(db, role_id) == {("project", str(live_project))}
