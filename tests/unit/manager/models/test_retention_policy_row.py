from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.manager.data.retention.types import RetentionCategory
from ai.backend.manager.models.base import populate_fixture
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
        # Retention is opt-in: rows default to disabled (server_default=false).
        assert row.enabled is False
        assert row.last_swept_at is None
        # created_at / updated_at come from LifecycleTimestampsMixin (server_default).
        assert row.created_at is not None
        assert row.updated_at is not None

    async def test_populate_fixture_converts_interval_kwargs_dict(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        fixture_data: dict[str, list[dict[str, object]]] = {
            "retention_policies": [
                {
                    "category": "usage_records",
                    "retention_period": {"days": 90},
                    "enabled": False,
                }
            ],
        }

        await populate_fixture(db, fixture_data)

        async with db.begin_readonly_session() as sess:
            row = (
                await sess.execute(
                    sa.select(RetentionPolicyRow).where(
                        RetentionPolicyRow.category == RetentionCategory.USAGE_RECORDS
                    )
                )
            ).scalar_one()
        assert row.retention_period == timedelta(days=90)
        assert row.enabled is False

    async def test_populate_fixture_converts_interval_seconds_number(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        fixture_data: dict[str, list[dict[str, object]]] = {
            "retention_policies": [
                {
                    "category": "logs",
                    "retention_period": 3600,
                    "enabled": False,
                }
            ],
        }

        await populate_fixture(db, fixture_data)

        async with db.begin_readonly_session() as sess:
            row = (
                await sess.execute(
                    sa.select(RetentionPolicyRow).where(
                        RetentionPolicyRow.category == RetentionCategory.LOGS
                    )
                )
            ).scalar_one()
        assert row.retention_period == timedelta(seconds=3600)

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
