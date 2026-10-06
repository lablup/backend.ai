"""Verify the target flag migration and access constraints against PostgreSQL."""

from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.ext.asyncio import AsyncConnection

from ai.backend.manager.models.alembic.versions.f7b1e5a9032c_add_image_commit_target_flag import (
    downgrade,
    upgrade,
)
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@pytest.fixture
async def legacy_conn(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[AsyncConnection]:
    async with database_connection.begin() as conn:
        await conn.execute(
            sa.text("""
            CREATE TEMP TABLE association_container_registries_groups (
                id UUID PRIMARY KEY,
                registry_id UUID NOT NULL,
                group_id UUID NOT NULL,
                CONSTRAINT uq_registry_id_group_id UNIQUE (registry_id, group_id)
            ) ON COMMIT DROP
        """)
        )
        yield conn


@pytest.fixture
async def migrated_conn(legacy_conn: AsyncConnection) -> AsyncConnection:
    await legacy_conn.run_sync(_upgrade)
    return legacy_conn


def _upgrade(conn: sa.Connection) -> None:
    with Operations.context(MigrationContext.configure(conn)):
        upgrade()


def _downgrade(conn: sa.Connection) -> None:
    with Operations.context(MigrationContext.configure(conn)):
        downgrade()


@pytest.fixture
def group_id() -> UUID:
    return uuid4()


async def test_defaults_existing_and_new_access_to_false(
    legacy_conn: AsyncConnection, group_id: UUID
) -> None:
    first_id, second_id = uuid4(), uuid4()
    insert = sa.text("""INSERT INTO association_container_registries_groups (id, registry_id, group_id)
        VALUES (:id, :registry_id, :group_id)""")
    await legacy_conn.execute(
        insert, {"id": first_id, "registry_id": uuid4(), "group_id": group_id}
    )
    await legacy_conn.run_sync(_upgrade)
    await legacy_conn.execute(
        insert, {"id": second_id, "registry_id": uuid4(), "group_id": group_id}
    )
    rows = (
        await legacy_conn.execute(
            sa.select(
                AssociationContainerRegistriesGroupsRow.id,
                AssociationContainerRegistriesGroupsRow.is_image_commit_target,
            )
        )
    ).all()
    assert {row_id: flagged for row_id, flagged in rows} == {first_id: False, second_id: False}


async def test_one_target_per_project_and_access_survives_clearing(
    migrated_conn: AsyncConnection, group_id: UUID
) -> None:
    first_id, second_id = uuid4(), uuid4()
    await migrated_conn.execute(
        sa.insert(AssociationContainerRegistriesGroupsRow),
        [
            {"id": first_id, "registry_id": uuid4(), "group_id": group_id},
            {"id": second_id, "registry_id": uuid4(), "group_id": group_id},
        ],
    )
    await migrated_conn.execute(
        sa.update(AssociationContainerRegistriesGroupsRow)
        .where(AssociationContainerRegistriesGroupsRow.id == first_id)
        .values(is_image_commit_target=True)
    )
    with pytest.raises(sa.exc.IntegrityError, match="uq_project_image_commit_target"):
        async with migrated_conn.begin_nested():
            await migrated_conn.execute(
                sa.update(AssociationContainerRegistriesGroupsRow)
                .where(AssociationContainerRegistriesGroupsRow.id == second_id)
                .values(is_image_commit_target=True)
            )
    await migrated_conn.execute(
        sa.insert(AssociationContainerRegistriesGroupsRow).values(
            id=uuid4(),
            registry_id=uuid4(),
            group_id=uuid4(),
            is_image_commit_target=True,
        )
    )
    await migrated_conn.execute(
        sa.update(AssociationContainerRegistriesGroupsRow)
        .where(AssociationContainerRegistriesGroupsRow.group_id == group_id)
        .values(is_image_commit_target=False)
    )
    rows = (
        await migrated_conn.execute(
            sa.select(
                AssociationContainerRegistriesGroupsRow.id,
                AssociationContainerRegistriesGroupsRow.is_image_commit_target,
            ).where(AssociationContainerRegistriesGroupsRow.group_id == group_id)
        )
    ).all()
    assert {row_id: flagged for row_id, flagged in rows} == {first_id: False, second_id: False}


async def test_not_null_and_existing_pair_uniqueness(
    migrated_conn: AsyncConnection, group_id: UUID
) -> None:
    registry_id = uuid4()
    await migrated_conn.execute(
        sa.insert(AssociationContainerRegistriesGroupsRow).values(
            id=uuid4(),
            registry_id=registry_id,
            group_id=group_id,
        )
    )
    with pytest.raises(sa.exc.IntegrityError, match="uq_registry_id_group_id"):
        async with migrated_conn.begin_nested():
            await migrated_conn.execute(
                sa.insert(AssociationContainerRegistriesGroupsRow).values(
                    id=uuid4(),
                    registry_id=registry_id,
                    group_id=group_id,
                )
            )
    with pytest.raises(sa.exc.IntegrityError, match="not-null constraint"):
        async with migrated_conn.begin_nested():
            await migrated_conn.execute(
                sa.insert(AssociationContainerRegistriesGroupsRow).values(
                    id=uuid4(),
                    registry_id=uuid4(),
                    group_id=group_id,
                    is_image_commit_target=None,
                )
            )


async def test_downgrade_preserves_access_rows(
    migrated_conn: AsyncConnection, group_id: UUID
) -> None:
    row_id, registry_id = uuid4(), uuid4()
    await migrated_conn.execute(
        sa.insert(AssociationContainerRegistriesGroupsRow).values(
            id=row_id,
            registry_id=registry_id,
            group_id=group_id,
            is_image_commit_target=True,
        )
    )
    await migrated_conn.run_sync(_downgrade)
    assert (
        await migrated_conn.execute(
            sa.text("SELECT id, registry_id, group_id FROM association_container_registries_groups")
        )
    ).one() == (row_id, registry_id, group_id)
    columns = await migrated_conn.run_sync(
        lambda conn: sa.inspect(conn).get_columns("association_container_registries_groups")
    )
    assert "is_image_commit_target" not in {column["name"] for column in columns}
    await migrated_conn.run_sync(_upgrade)
    assert (
        await migrated_conn.scalar(
            sa.select(AssociationContainerRegistriesGroupsRow.is_image_commit_target)
        )
        is False
    )
