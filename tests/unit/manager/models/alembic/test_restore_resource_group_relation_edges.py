"""Runs the resource group relation edge restore against a real database.

Static analysis does not reach the migration's SQL, so the backfill is exercised here:
an association standing without its edges goes in, the migration runs, and the edges it
wrote are read back.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.alembic.versions.c4b1f7e9a2d3_restore_resource_group_relation_edges import (
    add_relation_edges,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables

# Every association table the migration reads, with the tables their keys point at.
_TABLES: list[Table | type[HasTable]] = [
    DomainRow,
    ResourceGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRow,
    ProjectRow,
    KeyPairRow,
    ResourceGroupForDomainRow,
    ResourceGroupForProjectRow,
    ResourceGroupForKeypairsRow,
    VirtualEntityRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    ScopeBindingRow,
]


@dataclass
class _Fixture:
    """A pair whose nodes are both in the graph, and one whose group is not."""

    group_node: uuid.UUID
    domain_node: uuid.UUID
    unreachable_group_id: uuid.UUID


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def seeded(db: ExtendedAsyncSAEngine) -> _Fixture:
    group_id, domain_id, unreachable_group_id = (uuid.uuid4() for _ in range(3))
    async with db.begin_session() as session:
        session.add(DomainRow(name="relation-edge-domain", id=domain_id))
        session.add_all([
            ResourceGroupRow(
                name="relation-edge-group",
                id=group_id,
                driver="static",
                scheduler="fifo",
            ),
            ResourceGroupRow(
                name="relation-edge-group-off-graph",
                id=unreachable_group_id,
                driver="static",
                scheduler="fifo",
            ),
        ])
        group_node = VirtualEntityRow(entity_type=ResourceGroupEntityType(), entity_id=group_id)
        domain_node = VirtualEntityRow(entity_type=DomainEntityType(), entity_id=domain_id)
        session.add_all([group_node, domain_node])
        await session.flush()
        session.add_all([
            ResourceGroupForDomainRow(resource_group_id=group_id, domain_id=domain_id),
            ResourceGroupForDomainRow(resource_group_id=unreachable_group_id, domain_id=domain_id),
        ])
        await session.commit()
        return _Fixture(
            group_node=group_node.id,
            domain_node=domain_node.id,
            unreachable_group_id=unreachable_group_id,
        )


async def _run(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin() as conn:
        await conn.run_sync(add_relation_edges)


async def _read_edges(
    db: ExtendedAsyncSAEngine, group_node: uuid.UUID, domain_node: uuid.UUID
) -> tuple[list[Permission | None], list[bool], list[tuple[Permission, bool]]]:
    """The caps the domain governs the group under, whether each membership is capped,
    and the bits the group lends the domain."""
    async with db.begin_readonly_session() as session:
        caps = (
            await session.scalars(
                sa.select(ScopeBindingRow.permission_cap).where(
                    ScopeBindingRow.virtual_entity_id == group_node,
                    ScopeBindingRow.scope_entity_id == domain_node,
                )
            )
        ).all()
        memberships = (
            await session.scalars(
                sa.select(EntityMembershipRow).where(
                    EntityMembershipRow.virtual_entity_id == group_node,
                    EntityMembershipRow.member_entity_id == domain_node,
                )
            )
        ).all()
        lent = (
            await session.execute(
                sa.select(EntityMembershipCapRow.permission, EntityMembershipCapRow.all_fields)
                .join(
                    EntityMembershipRow,
                    EntityMembershipRow.id == EntityMembershipCapRow.membership_id,
                )
                .where(
                    EntityMembershipRow.virtual_entity_id == group_node,
                    EntityMembershipRow.member_entity_id == domain_node,
                )
            )
        ).all()
    return (
        list(caps),
        [membership.capped for membership in memberships],
        [(permission, all_fields) for permission, all_fields in lent],
    )


async def test_edges_are_written_for_an_association_that_lost_them(
    db: ExtendedAsyncSAEngine, seeded: _Fixture
) -> None:
    await _run(db)

    caps, capped, lent = await _read_edges(db, seeded.group_node, seeded.domain_node)
    assert caps == [Permission.READ]
    assert capped == [True]
    assert lent == [(Permission.READ, True)]


async def test_running_again_changes_nothing(db: ExtendedAsyncSAEngine, seeded: _Fixture) -> None:
    await _run(db)
    await _run(db)

    caps, capped, lent = await _read_edges(db, seeded.group_node, seeded.domain_node)
    assert caps == [Permission.READ]
    assert capped == [True]
    assert lent == [(Permission.READ, True)]


async def test_an_association_whose_group_has_no_node_is_left_alone(
    db: ExtendedAsyncSAEngine, seeded: _Fixture
) -> None:
    await _run(db)

    async with db.begin_readonly_session() as session:
        nodes = await session.scalar(
            sa.select(sa.func.count())
            .select_from(VirtualEntityRow)
            .where(VirtualEntityRow.entity_id == seeded.unreachable_group_id)
        )
        bindings = await session.scalar(
            sa.select(sa.func.count())
            .select_from(ScopeBindingRow)
            .where(ScopeBindingRow.scope_entity_id == seeded.domain_node)
        )
    assert nodes == 0
    assert bindings == 1
