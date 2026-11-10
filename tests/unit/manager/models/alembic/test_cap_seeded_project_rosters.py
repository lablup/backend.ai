"""Runs the project roster capping against a real database.

Static analysis does not reach the migration's SQL, so it is exercised here: roster
edges of both shapes go in, the migration runs, and what each edge lends is read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.alembic.versions.d3f9a2c81b47_cap_seeded_project_rosters import (
    cap_project_rosters,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

_TABLES: list[Table | type[HasTable]] = [
    VirtualEntityRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
]


@dataclass
class _Fixture:
    """A roster edge in each shape, and a domain's belonging edge beside them."""

    seeded: uuid.UUID
    runtime: uuid.UUID
    domain_member: uuid.UUID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def seeded(db: ExtendedAsyncSAEngine) -> _Fixture:
    async with db.begin_session() as session:
        project = VirtualEntityRow(entity_type=ProjectEntityType(), entity_id=uuid.uuid4())
        domain = VirtualEntityRow(entity_type=DomainEntityType(), entity_id=uuid.uuid4())
        seed_user = VirtualEntityRow(entity_type=UserEntityType(), entity_id=uuid.uuid4())
        runtime_user = VirtualEntityRow(entity_type=UserEntityType(), entity_id=uuid.uuid4())
        session.add_all([project, domain, seed_user, runtime_user])
        await session.flush()
        seed_edge = EntityMembershipRow(
            virtual_entity_id=project.id, member_entity_id=seed_user.id, capped=False
        )
        runtime_edge = EntityMembershipRow(
            virtual_entity_id=project.id, member_entity_id=runtime_user.id, capped=True
        )
        domain_edge = EntityMembershipRow(
            virtual_entity_id=domain.id, member_entity_id=seed_user.id, capped=False
        )
        session.add_all([seed_edge, runtime_edge, domain_edge])
        await session.flush()
        session.add(
            EntityMembershipCapRow(
                membership_id=runtime_edge.id, permission=Permission.READ, all_fields=True
            )
        )
        await session.commit()
        return _Fixture(seeded=seed_edge.id, runtime=runtime_edge.id, domain_member=domain_edge.id)


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(cap_project_rosters)


async def _read_edge(
    db: ExtendedAsyncSAEngine, membership_id: uuid.UUID
) -> tuple[bool, list[tuple[Permission, bool]]]:
    """Whether the edge is capped, and the bits it lends."""
    async with db.begin_readonly_session() as session:
        capped = await session.scalar(
            sa.select(EntityMembershipRow.capped).where(EntityMembershipRow.id == membership_id)
        )
        lent = (
            await session.execute(
                sa.select(EntityMembershipCapRow.permission, EntityMembershipCapRow.all_fields)
                .where(EntityMembershipCapRow.membership_id == membership_id)
                .order_by(EntityMembershipCapRow.permission)
            )
        ).all()
    assert capped is not None
    return capped, [(permission, all_fields) for permission, all_fields in lent]


async def test_a_seeded_roster_edge_is_capped_to_read(
    db: ExtendedAsyncSAEngine, seeded: _Fixture
) -> None:
    await _run(db)

    assert await _read_edge(db, seeded.seeded) == (True, [(Permission.READ, True)])


async def test_a_runtime_roster_edge_is_left_as_it_is(
    db: ExtendedAsyncSAEngine, seeded: _Fixture
) -> None:
    await _run(db)

    assert await _read_edge(db, seeded.runtime) == (True, [(Permission.READ, True)])


async def test_a_belonging_edge_outside_a_roster_is_left_as_it_is(
    db: ExtendedAsyncSAEngine, seeded: _Fixture
) -> None:
    await _run(db)

    assert await _read_edge(db, seeded.domain_member) == (False, [])


async def test_running_again_changes_nothing(db: ExtendedAsyncSAEngine, seeded: _Fixture) -> None:
    await _run(db)
    await _run(db)

    assert await _read_edge(db, seeded.seeded) == (True, [(Permission.READ, True)])
