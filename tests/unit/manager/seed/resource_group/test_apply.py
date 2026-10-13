"""`mgr seed apply` writes the resource group file through the resource group upserter."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType, ResourceGroupID
from ai.backend.manager.models.resource_group.creators import ResourceGroupCreator
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.resource_group.seed import ResourceGroupSeed
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

# A graph edge with each end named by its entity, the resource group under test as "self".
type _Edge = tuple[str, str, str]


@pytest.fixture
def plan(resource_group_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([resource_group_seed_dir])


@pytest.fixture
async def runtime_resource_group_id(db: ExtendedAsyncSAEngine) -> ResourceGroupID:
    """A resource group created the way the resource group service creates one."""
    async with SeedOpsProvider(db).write_ops() as w:
        data = await w.create_role_managed_entity(
            ResourceGroupCreator(name="runtime", driver="static", scheduler="fifo")
        )
    return ResourceGroupID(data.id)


async def _groups(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, str | None, bool, bool]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                ResourceGroupRow.id,
                ResourceGroupRow.name,
                ResourceGroupRow.description,
                ResourceGroupRow.is_active,
                ResourceGroupRow.is_default,
            )
        )
        return {
            str(row.id): (row.name, row.description, row.is_active, row.is_default) for row in rows
        }


async def _edges(db: ExtendedAsyncSAEngine, resource_group_id: uuid.UUID) -> set[_Edge]:
    """The ownership and governance edges touching the resource group's node."""
    async with db.begin_readonly() as conn:
        nodes = {
            row.id: (str(row.entity_type), str(row.entity_id))
            for row in await conn.execute(
                sa.select(
                    VirtualEntityRow.id, VirtualEntityRow.entity_type, VirtualEntityRow.entity_id
                )
            )
        }
        memberships = (
            await conn.execute(
                sa.select(
                    EntityMembershipRow.virtual_entity_id, EntityMembershipRow.member_entity_id
                )
            )
        ).all()
        bindings = (
            await conn.execute(
                sa.select(ScopeBindingRow.virtual_entity_id, ScopeBindingRow.scope_entity_id)
            )
        ).all()
    group_node = (str(ResourceGroupEntityType()), str(resource_group_id))

    def name(node_id: uuid.UUID) -> str:
        node = nodes[node_id]
        return "self" if node == group_node else ":".join(node)

    edges: set[_Edge] = set()
    for relation, rows in (("owns", memberships), ("governs", bindings)):
        for owner, member in rows:
            if group_node in (nodes[owner], nodes[member]):
                edges.add((relation, name(owner), name(member)))
    return edges


def _seeds(plan: SeedPlan) -> list[ResourceGroupSeed]:
    return [item for item in plan.batches[0].items() if isinstance(item, ResourceGroupSeed)]


def _default(plan: SeedPlan, default_resource_group_id: str) -> ResourceGroupSeed:
    return next(seed for seed in _seeds(plan) if str(seed.id) == default_resource_group_id)


class TestApply:
    async def test_an_empty_database_gets_the_seed_rows(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert len(results[SeedKind.RESOURCE_GROUP].succeeded) == len(_seeds(plan))
        assert results[SeedKind.RESOURCE_GROUP].skipped == []
        assert await _groups(db) == {
            str(seed.id): (seed.name, seed.description, seed.is_active, seed.is_default)
            for seed in _seeds(plan)
        }

    async def test_a_seeded_group_has_the_graph_edges_of_a_created_one(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        runtime_resource_group_id: ResourceGroupID,
        default_resource_group_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)

        created = await _edges(db, runtime_resource_group_id)
        assert created
        assert await _edges(db, uuid.UUID(default_resource_group_id)) == created

    async def test_an_existing_group_is_skipped_and_left_as_it_is(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        default_resource_group_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ResourceGroupRow)
                .where(ResourceGroupRow.id == default_resource_group_id)
                .values(description="edited")
            )
        edges = await _edges(db, uuid.UUID(default_resource_group_id))

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.RESOURCE_GROUP].succeeded == []
        assert len(results[SeedKind.RESOURCE_GROUP].skipped) == len(_seeds(plan))
        assert (await _groups(db))[default_resource_group_id][1] == "edited"
        assert await _edges(db, uuid.UUID(default_resource_group_id)) == edges

    async def test_a_skipped_group_missing_from_the_graph_is_put_into_it(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        runtime_resource_group_id: ResourceGroupID,
        default_resource_group_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.delete(VirtualEntityRow).where(
                    VirtualEntityRow.entity_type == ResourceGroupEntityType(),
                    VirtualEntityRow.entity_id == default_resource_group_id,
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.RESOURCE_GROUP].succeeded == []
        assert await _edges(db, uuid.UUID(default_resource_group_id)) == await _edges(
            db, runtime_resource_group_id
        )

    async def test_overwrite_restores_the_seed_values_and_keeps_the_name(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        default_resource_group_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        groups = await _groups(db)
        edges = await _edges(db, uuid.UUID(default_resource_group_id))
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(ResourceGroupRow)
                .where(ResourceGroupRow.id == default_resource_group_id)
                .values(description="edited", is_active=False, is_default=False)
            )
        renamed = _default(plan, default_resource_group_id).model_copy(update={"name": "renamed"})

        results = await repository.partial_write([renamed.write()], overwrite=True)

        assert [result.written for result in results] == [True]
        assert await _groups(db) == groups
        assert await _edges(db, uuid.UUID(default_resource_group_id)) == edges

    async def test_a_name_held_by_another_group_skips_the_item(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        runtime_resource_group_id: ResourceGroupID,
    ) -> None:
        [seed, *_] = _seeds(plan)
        taken = seed.model_copy(update={"name": "runtime"})

        [result] = await repository.partial_write([taken.write()], overwrite=False)

        assert result.error is not None
        assert str(seed.id) not in await _groups(db)

    async def test_a_second_item_repeating_a_name_fails_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        first, second = _seeds(plan)
        repeated = second.model_copy(update={"name": first.name})

        results = await repository.partial_write([first.write(), repeated.write()], overwrite=False)

        assert [result.error is None for result in results] == [True, False]
        assert set(await _groups(db)) == {str(first.id)}

    async def test_a_second_default_fails_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        default_resource_group_id: str,
    ) -> None:
        default = _default(plan, default_resource_group_id)
        [other] = [seed for seed in _seeds(plan) if str(seed.id) != default_resource_group_id]
        second_default = other.model_copy(update={"is_default": True})

        results = await repository.partial_write(
            [default.write(), second_default.write()], overwrite=False
        )

        assert [result.error is None for result in results] == [True, False]
        assert set(await _groups(db)) == {default_resource_group_id}
