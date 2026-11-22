"""Runs the session group admission migration against a real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa
from sqlalchemy import Table
from sqlalchemy.engine import Connection

from ai.backend.manager.models.alembic.versions import (
    dc09f3d488de_add_session_group_admission as revision,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserRow,
    ProjectRow,
    SessionGroupRow,
]


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine]:
    async with with_tables(database_connection, _TABLES):
        async with database_connection.begin() as conn:
            await conn.run_sync(revision.drop_admission_columns)
        yield database_connection


def _schema(conn: Connection) -> tuple[set[str], set[str]]:
    inspector = sa.inspect(conn)
    columns = {column["name"] for column in inspector.get_columns("session_groups")}
    checks = {
        check["name"]
        for check in inspector.get_check_constraints("session_groups")
        if check["name"]
    }
    return columns, checks


class TestAddSessionGroupAdmission:
    async def test_the_columns_and_the_check_are_added(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin() as conn:
            await conn.run_sync(revision.add_admission_columns)
            columns, checks = await conn.run_sync(_schema)

        assert {"admission", "member_count"} <= columns
        assert revision.MEMBER_COUNT_CHECK in checks

    async def test_running_it_twice_leaves_the_same_schema(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin() as conn:
            await conn.run_sync(revision.add_admission_columns)
            once = await conn.run_sync(_schema)
            await conn.run_sync(revision.add_admission_columns)
            twice = await conn.run_sync(_schema)

        assert once == twice

    async def test_the_downgrade_removes_both_columns(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin() as conn:
            await conn.run_sync(revision.add_admission_columns)
            await conn.run_sync(revision.drop_admission_columns)
            columns, checks = await conn.run_sync(_schema)

        assert not {"admission", "member_count"} & columns
        assert revision.MEMBER_COUNT_CHECK not in checks
