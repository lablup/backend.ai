"""Verify that the association column rename preserves rows and constraints."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Callable

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection

from ai.backend.manager.models.alembic.versions import (
    f55b5bb47fef_rename_registry_association_group_id_to_project_id as migration,
)
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables

_metadata = sa.MetaData()
_projects = sa.Table("groups", _metadata, sa.Column("id", GUID, primary_key=True))
_registries = sa.Table("container_registries", _metadata, sa.Column("id", GUID, primary_key=True))
_associations = sa.Table(
    "association_container_registries_groups",
    _metadata,
    sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
    sa.Column(
        "registry_id",
        GUID,
        sa.ForeignKey("container_registries.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "group_id",
        GUID,
        sa.ForeignKey(
            "groups.id",
            name="fk_association_container_registries_groups_group_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    ),
    sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.UniqueConstraint("registry_id", "group_id", name="uq_registry_id_group_id"),
    sa.Index(
        "uq_project_default_registry",
        "group_id",
        unique=True,
        postgresql_where=sa.text("is_default"),
    ),
)


def _run_migration(conn: Connection, operation: Callable[[], None]) -> None:
    with Operations.context(MigrationContext.configure(conn)):
        operation()


@pytest.fixture
async def legacy_associations(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[AsyncConnection, None]:
    async with with_tables(database_connection, [_projects, _registries, _associations]):
        async with database_connection.begin() as conn:
            projects = [uuid.uuid4(), uuid.uuid4()]
            registries = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
            await conn.execute(_projects.insert(), [{"id": value} for value in projects])
            await conn.execute(_registries.insert(), [{"id": value} for value in registries])
            await conn.execute(
                _associations.insert(),
                [
                    {"group_id": projects[0], "registry_id": registries[0], "is_default": True},
                    {"group_id": projects[0], "registry_id": registries[1], "is_default": False},
                    {"group_id": projects[1], "registry_id": registries[0], "is_default": True},
                ],
            )
            yield conn


class TestRenameRegistryAssociationProjectId:
    async def test_upgrade_downgrade_preserves_data_and_constraints(
        self, legacy_associations: AsyncConnection
    ) -> None:
        conn = legacy_associations
        before = (await conn.execute(sa.select(_associations).order_by(_associations.c.id))).all()
        spare_registry = await conn.scalar(
            sa.select(_registries.c.id).where(
                _registries.c.id.not_in(sa.select(_associations.c.registry_id))
            )
        )
        for operation, column, other_column in (
            (migration.upgrade, "project_id", "group_id"),
            (migration.downgrade, "group_id", "project_id"),
            (migration.upgrade, "project_id", "group_id"),
        ):
            await conn.run_sync(_run_migration, operation)
            after = (
                await conn.execute(
                    sa.text(
                        f"SELECT id, registry_id, {column}, is_default "
                        "FROM association_container_registries_groups ORDER BY id"
                    )
                )
            ).all()
            assert after == before

            def inspect_constraints(sync_conn: Connection) -> None:
                inspector = sa.inspect(sync_conn)
                table = _associations.name
                columns = {item["name"] for item in inspector.get_columns(table)}
                assert column in columns
                assert other_column not in columns
                constraints = inspector.get_unique_constraints(table)
                assert any(
                    item["name"] == f"uq_registry_id_{column}"
                    and item["column_names"] == ["registry_id", column]
                    for item in constraints
                )
                indexes = inspector.get_indexes(table)
                index = next(
                    item for item in indexes if item["name"] == "uq_project_default_registry"
                )
                assert index["unique"]
                assert index["column_names"] == [column]
                assert index["dialect_options"]["postgresql_where"] == "is_default"
                foreign_keys = inspector.get_foreign_keys(table)
                assert any(
                    item["name"] == f"fk_association_container_registries_groups_{column}"
                    and item["constrained_columns"] == [column]
                    and item["options"]["ondelete"] == "CASCADE"
                    for item in foreign_keys
                )

            await conn.run_sync(inspect_constraints)
            row = next(item for item in after if item.is_default)
            # Reject a duplicate pair, another default registry, and a missing project.
            for project_id, registry_id, is_default, constraint in (
                (row[2], row.registry_id, False, f"uq_registry_id_{column}"),
                (
                    row[2],
                    spare_registry,
                    True,
                    "uq_project_default_registry",
                ),
                (
                    uuid.uuid4(),
                    row.registry_id,
                    False,
                    f"fk_association_container_registries_groups_{column}",
                ),
            ):
                with pytest.raises(sa.exc.IntegrityError, match=constraint):
                    async with conn.begin_nested():
                        await conn.execute(
                            sa.text(
                                f"INSERT INTO association_container_registries_groups ({column}, registry_id, is_default) "
                                "VALUES (:project_id, :registry_id, :is_default)"
                            ),
                            {
                                "project_id": project_id,
                                "registry_id": registry_id,
                                "is_default": is_default,
                            },
                        )
