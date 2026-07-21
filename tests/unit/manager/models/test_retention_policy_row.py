from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.manager.data.retention.types import RetentionCategory
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


class TestRetentionCategory:
    def test_has_the_eight_catalog_categories(self) -> None:
        assert {c.value for c in RetentionCategory} == {
            "logs",
            "login",
            "reconcile_history",
            "roles_invitations",
            "deployments",
            "sessions",
            "usage_records",
            "usage_buckets",
        }

    def test_unknown_category_string_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            RetentionCategory("unknown_category")


class TestRetentionPolicyRow:
    @pytest.fixture
    async def db(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, [RetentionPolicyRow]):
            yield database_connection

    async def test_insert_and_read_back(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin_session() as sess:
            sess.add(
                RetentionPolicyRow(
                    category=RetentionCategory.USAGE_RECORDS,
                    retention_period=timedelta(days=90),
                )
            )

        async with db.begin_readonly_session() as sess:
            row = (
                await sess.execute(
                    sa.select(RetentionPolicyRow).where(
                        RetentionPolicyRow.category == RetentionCategory.USAGE_RECORDS
                    )
                )
            ).scalar_one()
        assert row.category is RetentionCategory.USAGE_RECORDS
        assert row.retention_period == timedelta(days=90)
        assert row.enabled is True
        assert row.last_swept_at is None
        # created_at / updated_at come from LifecycleTimestampsMixin (server_default).
        assert row.created_at is not None
        assert row.updated_at is not None

    async def test_duplicate_category_violates_unique(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin_session() as sess:
            sess.add(
                RetentionPolicyRow(
                    category=RetentionCategory.LOGS,
                    retention_period=timedelta(days=365),
                )
            )

        with pytest.raises(IntegrityError):
            async with db.begin_session() as sess:
                sess.add(
                    RetentionPolicyRow(
                        category=RetentionCategory.LOGS,
                        retention_period=timedelta(days=365),
                    )
                )
