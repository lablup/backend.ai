"""Verifies the projects retention policy seed migration against a real database."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import timedelta
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.manager.data.retention.types import RetentionCategory
from ai.backend.manager.models.alembic.versions.b7d2a91c4e58_seed_projects_retention_policy import (
    seed,
)
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


class TestProjectsRetentionPolicySeed:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, [RetentionPolicyRow]):
            yield database_connection

    async def _run_seed(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin() as conn:
            await conn.run_sync(seed)

    async def _projects_policies(self, db: ExtendedAsyncSAEngine) -> list[RetentionPolicyRow]:
        async with db.begin_readonly_session() as sess:
            return list(
                (
                    await sess.scalars(
                        sa.select(RetentionPolicyRow).where(
                            RetentionPolicyRow.category == RetentionCategory.PROJECTS
                        )
                    )
                ).all()
            )

    async def test_seeds_the_projects_policy_disabled_for_a_month(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await self._run_seed(db)

        policies = await self._projects_policies(db)
        assert len(policies) == 1
        assert policies[0].id == RetentionPolicyID(UUID("b1e5f4a0-0009-4c10-8a01-000000000009"))
        assert policies[0].retention_period == timedelta(days=30)
        assert policies[0].enabled is False

    async def test_running_twice_leaves_one_row(self, db: ExtendedAsyncSAEngine) -> None:
        await self._run_seed(db)
        await self._run_seed(db)

        assert len(await self._projects_policies(db)) == 1

    async def test_an_existing_row_is_not_overwritten(self, db: ExtendedAsyncSAEngine) -> None:
        existing = RetentionPolicyRow(
            category=RetentionCategory.PROJECTS,
            retention_period=timedelta(days=365),
            enabled=True,
        )
        async with db.begin_session() as sess:
            sess.add(existing)
            await sess.flush()
            existing_id = existing.id

        await self._run_seed(db)

        policies = await self._projects_policies(db)
        assert len(policies) == 1
        assert policies[0].id == existing_id
        assert policies[0].retention_period == timedelta(days=365)
        assert policies[0].enabled is True
