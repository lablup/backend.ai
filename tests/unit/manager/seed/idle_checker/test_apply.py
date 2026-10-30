"""`mgr seed apply` writes the checkers through the idle checker upserter."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind


@pytest.fixture
def plan(idle_checker_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([idle_checker_seed_dir])


async def _checkers(db: ExtendedAsyncSAEngine) -> dict[str, tuple[str, int]]:
    """Each checker id with its name and grace period."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                IdleCheckerRow.id, IdleCheckerRow.name, IdleCheckerRow.initial_grace_period_seconds
            )
        )
        return {str(row.id): (row.name, row.initial_grace_period_seconds) for row in rows}


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The checkers the global node holds as members."""
    global_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == GlobalEntityType(),
            VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.GLOBAL),
        )
        .scalar_subquery()
    )
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(VirtualEntityRow.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == VirtualEntityRow.id)
            .where(
                EntityMembershipRow.virtual_entity_id == global_node,
                VirtualEntityRow.entity_type == "idle_checker",
            )
        )
        return {str(row.entity_id) for row in rows}


async def _insert_renamed(db: ExtendedAsyncSAEngine, checker_id: str) -> None:
    """A row under a seeded id that states other values."""
    async with db.begin_session() as sess:
        await sess.execute(
            sa.insert(IdleCheckerRow).values(
                id=IdleCheckerID(UUID(checker_id)),
                name="renamed",
                target_session_types=[SessionTypes.BATCH],
                initial_grace_period_seconds=10,
                spec=IdleCheckerSpec(
                    type=CheckerType.SESSION_LIFETIME,
                    session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=1),
                ),
            )
        )


class TestApply:
    async def test_an_empty_database_gets_every_checker(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        idle_checker_ids: list[str],
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.IDLE_CHECKER].succeeded == idle_checker_ids
        assert await _checkers(db) == {
            idle_checker_ids[0]: ("session-lifetime", 0),
            idle_checker_ids[1]: ("network-timeout", 300),
        }

    async def test_the_checker_type_follows_the_spec(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_readonly() as conn:
            rows = await conn.execute(sa.select(IdleCheckerRow.name, IdleCheckerRow.checker_type))
            assert dict(rows.tuples().all()) == {
                "session-lifetime": CheckerType.SESSION_LIFETIME,
                "network-timeout": CheckerType.NETWORK_TIMEOUT,
            }

    async def test_a_created_checker_is_created_in_global(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        idle_checker_ids: list[str],
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == set(idle_checker_ids)

    async def test_an_existing_checker_is_skipped_and_kept(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        idle_checker_ids: list[str],
    ) -> None:
        await _insert_renamed(db, idle_checker_ids[0])

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.IDLE_CHECKER].succeeded == [idle_checker_ids[1]]
        assert [failure.reason for failure in results[SeedKind.IDLE_CHECKER].skipped] == ["exists"]
        assert (await _checkers(db))[idle_checker_ids[0]] == ("renamed", 10)

    async def test_an_overwrite_rewrites_the_checker_under_its_id(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        idle_checker_ids: list[str],
    ) -> None:
        await _insert_renamed(db, idle_checker_ids[0])

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.IDLE_CHECKER].succeeded == idle_checker_ids
        assert (await _checkers(db))[idle_checker_ids[0]] == ("session-lifetime", 0)
        assert idle_checker_ids[0] in await _global_members(db)
