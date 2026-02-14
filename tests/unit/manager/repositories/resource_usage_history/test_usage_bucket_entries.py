"""Tests for UsageBucketEntryRow and normalized bucket entry operations.

Phase 3 (BA-4308): Verifies that usage bucket entries are correctly created,
upserted, and aggregated via the normalized usage_bucket_entries table.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UsageBucketEntryRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_usage_history.db_source.db_source import (
    ResourceUsageHistoryDBSource,
)
from ai.backend.manager.sokovan.scheduler.fair_share.aggregator import (
    DomainUsageBucketKey,
    UsageBucketAggregationResult,
    UserUsageBucketKey,
)
from ai.backend.testutils.db import with_tables


class TestUsageBucketEntries:
    """Test cases for normalized usage_bucket_entries table."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                DomainUsageBucketRow,
                ProjectUsageBucketRow,
                UserUsageBucketRow,
                UsageBucketEntryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()
        return domain_name

    @pytest.fixture
    async def db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ResourceUsageHistoryDBSource:
        return ResourceUsageHistoryDBSource(db_with_cleanup)

    @pytest.mark.asyncio
    async def test_increment_domain_buckets_creates_entries(
        self,
        db_source: ResourceUsageHistoryDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> None:
        """Verify that incrementing domain buckets also writes normalized entries."""
        delta = ResourceSlot({"cpu": Decimal("600"), "mem": Decimal("4096000")})
        period = date(2024, 1, 15)

        result = UsageBucketAggregationResult(
            user_usage_deltas={},
            project_usage_deltas={},
            domain_usage_deltas={
                DomainUsageBucketKey(
                    domain_name=test_domain_name,
                    resource_group="default",
                    period_date=period,
                ): delta,
            },
        )

        await db_source.increment_usage_buckets(result)

        # Verify entries were created
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            entry_rows = (
                (
                    await db_sess.execute(
                        sa.select(UsageBucketEntryRow).where(
                            UsageBucketEntryRow.bucket_type == "domain"
                        )
                    )
                )
                .scalars()
                .all()
            )

            assert len(entry_rows) == 2
            slot_map = {e.slot_name: e for e in entry_rows}
            assert "cpu" in slot_map
            assert "mem" in slot_map
            assert slot_map["cpu"].amount == Decimal("600")
            assert slot_map["mem"].amount == Decimal("4096000")
            assert slot_map["cpu"].duration_seconds == 86400

    @pytest.mark.asyncio
    async def test_increment_accumulates_entries(
        self,
        db_source: ResourceUsageHistoryDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> None:
        """Verify that multiple increments accumulate in entries."""
        period = date(2024, 1, 15)
        key = DomainUsageBucketKey(
            domain_name=test_domain_name,
            resource_group="default",
            period_date=period,
        )

        # First increment
        delta1 = ResourceSlot({"cpu": Decimal("300")})
        result1 = UsageBucketAggregationResult(
            user_usage_deltas={},
            project_usage_deltas={},
            domain_usage_deltas={key: delta1},
        )
        await db_source.increment_usage_buckets(result1)

        # Second increment
        delta2 = ResourceSlot({"cpu": Decimal("200")})
        result2 = UsageBucketAggregationResult(
            user_usage_deltas={},
            project_usage_deltas={},
            domain_usage_deltas={key: delta2},
        )
        await db_source.increment_usage_buckets(result2)

        # Verify accumulated
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            entry_rows = (
                (
                    await db_sess.execute(
                        sa.select(UsageBucketEntryRow).where(
                            UsageBucketEntryRow.bucket_type == "domain"
                        )
                    )
                )
                .scalars()
                .all()
            )

            assert len(entry_rows) == 1
            assert entry_rows[0].slot_name == "cpu"
            assert entry_rows[0].amount == Decimal("500")

    @pytest.mark.asyncio
    async def test_increment_user_buckets_creates_entries(
        self,
        db_source: ResourceUsageHistoryDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> None:
        """Verify that incrementing user buckets also writes normalized entries."""
        user_uuid = uuid.uuid4()
        project_id = uuid.uuid4()
        delta = ResourceSlot({"cpu": Decimal("900"), "cuda.device": Decimal("1200")})
        period = date(2024, 1, 15)

        result = UsageBucketAggregationResult(
            user_usage_deltas={
                UserUsageBucketKey(
                    user_uuid=user_uuid,
                    project_id=project_id,
                    domain_name=test_domain_name,
                    resource_group="default",
                    period_date=period,
                ): delta,
            },
            project_usage_deltas={},
            domain_usage_deltas={},
        )

        await db_source.increment_usage_buckets(result)

        # Verify entries were created
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            entry_rows = (
                (
                    await db_sess.execute(
                        sa.select(UsageBucketEntryRow).where(
                            UsageBucketEntryRow.bucket_type == "user"
                        )
                    )
                )
                .scalars()
                .all()
            )

            assert len(entry_rows) == 2
            slot_map = {e.slot_name: e for e in entry_rows}
            assert slot_map["cpu"].amount == Decimal("900")
            assert slot_map["cuda.device"].amount == Decimal("1200")

    @pytest.mark.asyncio
    async def test_aggregated_usage_reads_from_entries(
        self,
        db_source: ResourceUsageHistoryDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> None:
        """Verify that aggregation queries read from normalized entries."""
        period1 = date(2024, 1, 15)
        period2 = date(2024, 1, 16)

        # Insert two domain buckets with entries
        result = UsageBucketAggregationResult(
            user_usage_deltas={},
            project_usage_deltas={},
            domain_usage_deltas={
                DomainUsageBucketKey(
                    domain_name=test_domain_name,
                    resource_group="default",
                    period_date=period1,
                ): ResourceSlot({"cpu": Decimal("600")}),
                DomainUsageBucketKey(
                    domain_name=test_domain_name,
                    resource_group="default",
                    period_date=period2,
                ): ResourceSlot({"cpu": Decimal("400")}),
            },
        )
        await db_source.increment_usage_buckets(result)

        # Query aggregated usage
        aggregated = await db_source.get_aggregated_usage_by_domain(
            resource_group="default",
            lookback_start=date(2024, 1, 14),
            lookback_end=date(2024, 1, 17),
        )

        assert test_domain_name in aggregated
        assert aggregated[test_domain_name]["cpu"] == Decimal("1000")
