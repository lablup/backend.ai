"""`mgr seed apply` writes the domain files through the domain upserter."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.domain.seed import DomainSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

# A graph edge with each end named by its entity, the domain under test as "self".
type _Edge = tuple[str, str, str]


@pytest.fixture
def plan(domain_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([domain_seed_dir])


@pytest.fixture
async def runtime_domain_id(db: ExtendedAsyncSAEngine) -> DomainID:
    """A domain created the way the domain service creates one."""
    async with SeedOpsProvider(db).write_ops() as w:
        data = await w.create_role_managed_entity(DomainCreator(name="runtime"))
    return DomainID(data.id)


async def _domains(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, str | None, bool, bool]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                DomainRow.id,
                DomainRow.name,
                DomainRow.description,
                DomainRow.is_active,
                DomainRow.is_default,
            )
        )
        return {
            str(row.id): (row.name, row.description, row.is_active, row.is_default) for row in rows
        }


async def _edges(db: ExtendedAsyncSAEngine, domain_id: uuid.UUID) -> set[_Edge]:
    """The ownership and governance edges touching the domain's node."""
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
    domain_node = (str(DomainEntityType()), str(domain_id))

    def name(node_id: uuid.UUID) -> str:
        node = nodes[node_id]
        return "self" if node == domain_node else ":".join(node)

    edges: set[_Edge] = set()
    for relation, rows in (("owns", memberships), ("governs", bindings)):
        for owner, member in rows:
            if domain_node in (nodes[owner], nodes[member]):
                edges.add((relation, name(owner), name(member)))
    return edges


def _seeds(plan: SeedPlan) -> list[DomainSeed]:
    return [item for item in plan.batches[0].items() if isinstance(item, DomainSeed)]


class TestApply:
    async def test_an_empty_database_gets_the_seed_rows(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert len(results[SeedKind.DOMAIN].succeeded) == len(_seeds(plan))
        assert results[SeedKind.DOMAIN].skipped == []
        assert await _domains(db) == {
            str(seed.id): (seed.name, seed.description, seed.is_active, seed.is_default)
            for seed in _seeds(plan)
        }

    async def test_a_seeded_domain_has_the_graph_edges_of_a_created_one(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        runtime_domain_id: DomainID,
        default_domain_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)

        created = await _edges(db, runtime_domain_id)
        assert created
        assert await _edges(db, uuid.UUID(default_domain_id)) == created

    async def test_an_existing_domain_is_skipped_and_left_as_it_is(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        default_domain_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(DomainRow)
                .where(DomainRow.id == default_domain_id)
                .values(description="edited")
            )
        edges = await _edges(db, uuid.UUID(default_domain_id))

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.DOMAIN].succeeded == []
        assert len(results[SeedKind.DOMAIN].skipped) == len(_seeds(plan))
        assert (await _domains(db))[default_domain_id][1] == "edited"
        assert await _edges(db, uuid.UUID(default_domain_id)) == edges

    async def test_a_skipped_domain_missing_from_the_graph_is_put_into_it(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        runtime_domain_id: DomainID,
        default_domain_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.delete(VirtualEntityRow).where(
                    VirtualEntityRow.entity_type == DomainEntityType(),
                    VirtualEntityRow.entity_id == default_domain_id,
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.DOMAIN].succeeded == []
        assert await _edges(db, uuid.UUID(default_domain_id)) == await _edges(db, runtime_domain_id)

    async def test_overwrite_restores_the_seed_values_and_keeps_the_name(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        default_domain_id: str,
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        domains = await _domains(db)
        edges = await _edges(db, uuid.UUID(default_domain_id))
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(DomainRow)
                .where(DomainRow.id == default_domain_id)
                .values(description="edited", is_active=False, is_default=False)
            )
        renamed = next(seed for seed in _seeds(plan) if str(seed.id) == default_domain_id)
        renamed = renamed.model_copy(update={"name": "renamed"})

        results = await repository.partial_write([renamed.write()], overwrite=True)

        assert [result.written for result in results] == [True]
        assert await _domains(db) == domains
        assert await _edges(db, uuid.UUID(default_domain_id)) == edges

    async def test_a_name_held_by_another_domain_skips_the_item(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        runtime_domain_id: DomainID,
    ) -> None:
        [seed, *_] = _seeds(plan)
        taken = seed.model_copy(update={"name": "runtime"})

        [result] = await repository.partial_write([taken.write()], overwrite=False)

        assert result.error is not None
        assert str(seed.id) not in await _domains(db)

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
        assert set(await _domains(db)) == {str(first.id)}

    async def test_a_second_default_fails_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        default_domain_id: str,
    ) -> None:
        [default] = [seed for seed in _seeds(plan) if str(seed.id) == default_domain_id]
        [other] = [seed for seed in _seeds(plan) if str(seed.id) != default_domain_id]
        second_default = other.model_copy(update={"is_default": True})

        results = await repository.partial_write(
            [default.write(), second_default.write()], overwrite=False
        )

        assert [result.error is None for result in results] == [True, False]
        assert set(await _domains(db)) == {default_domain_id}
