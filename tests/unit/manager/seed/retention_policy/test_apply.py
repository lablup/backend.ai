"""`mgr seed apply` writes the policies through the retention policy upserter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_LOGS = "0198a5a0-0000-7000-8000-00000000d001"
_USAGE_RECORDS = "0198a5a0-0000-7000-8000-00000000d002"


@pytest.fixture
def plan(retention_policy_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([retention_policy_seed_dir])


async def _policies(db: ExtendedAsyncSAEngine) -> dict[str, dict[str, Any]]:
    """Each policy by its id, with the columns the seed states and ``last_swept_at``."""
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                RetentionPolicyRow.id,
                RetentionPolicyRow.category,
                RetentionPolicyRow.retention_period,
                RetentionPolicyRow.enabled,
                RetentionPolicyRow.last_swept_at,
            )
        )
        return {
            str(row.id): {
                "category": row.category,
                "retention_period": row.retention_period,
                "enabled": row.enabled,
                "last_swept_at": row.last_swept_at,
            }
            for row in rows
        }


async def _global_members(db: ExtendedAsyncSAEngine) -> set[str]:
    """The policies the global node holds as members."""
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
                VirtualEntityRow.entity_type == "retention_policy",
            )
        )
        return {str(row.entity_id) for row in rows}


class TestApply:
    async def test_an_empty_database_gets_every_policy(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.RETENTION_POLICY].succeeded == [_LOGS, _USAGE_RECORDS]
        policies = await _policies(db)
        assert policies[_LOGS] == {
            "category": RetentionCategory.LOGS,
            "retention_period": timedelta(days=365),
            "enabled": False,
            "last_swept_at": None,
        }
        assert policies[_USAGE_RECORDS]["retention_period"] == timedelta(days=90)

    async def test_a_created_policy_is_created_in_global(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        assert await _global_members(db) == {_LOGS, _USAGE_RECORDS}

    async def test_an_existing_policy_is_skipped_and_kept(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RetentionPolicyRow)
                .where(RetentionPolicyRow.id == _LOGS)
                .values(enabled=True)
            )

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.RETENTION_POLICY].succeeded == []
        assert [failure.reason for failure in results[SeedKind.RETENTION_POLICY].skipped] == [
            "exists",
            "exists",
        ]
        assert (await _policies(db))[_LOGS]["enabled"] is True

    async def test_an_overwrite_restates_the_policy_and_keeps_last_swept_at(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        await SeedApplier(repository).apply(plan, overwrite=False)
        swept_at = datetime(2026, 1, 1, tzinfo=UTC)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RetentionPolicyRow)
                .where(RetentionPolicyRow.id == _LOGS)
                .values(retention_period=timedelta(days=7), enabled=True, last_swept_at=swept_at)
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.RETENTION_POLICY].succeeded == [_LOGS, _USAGE_RECORDS]
        assert (await _policies(db))[_LOGS] == {
            "category": RetentionCategory.LOGS,
            "retention_period": timedelta(days=365),
            "enabled": False,
            "last_swept_at": swept_at,
        }

    async def test_a_category_held_by_another_policy_skips_only_that_item(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, plan: SeedPlan
    ) -> None:
        """A row the seed did not write holds ``logs``; the unique category refuses the
        seed's ``logs`` policy and leaves the other written."""
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(RetentionPolicyRow).values(
                    category=RetentionCategory.LOGS,
                    retention_period=timedelta(days=30),
                    enabled=True,
                )
            )

        results = await SeedApplier(repository).apply(plan, overwrite=True)

        assert results[SeedKind.RETENTION_POLICY].succeeded == [_USAGE_RECORDS]
        assert [failure.key for failure in results[SeedKind.RETENTION_POLICY].skipped] == [_LOGS]
        assert results[SeedKind.RETENTION_POLICY].failed == []
        policies = await _policies(db)
        assert _LOGS not in policies
        assert _USAGE_RECORDS in policies
