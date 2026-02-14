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
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UsageBucketEntryRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_usage_history.db_source.db_source import (
    ResourceUsageHistoryDBSource,
)
from ai.backend.manager.sokovan.scheduler.fair_share.aggregator import (
    BucketDelta,
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
                # Base rows in FK dependency order (parents before children)
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AgentRow,
                ImageRow,
                SessionRow,
                KernelRow,
                # Resource Usage History rows
                KernelUsageRecordRow,
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
                total_resource_slots=ResourceSlot(),
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
        raw_slots = ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096000")})
        duration = 300  # 5-minute slice
        period = date(2024, 1, 15)

        result = UsageBucketAggregationResult(
            user_usage_deltas={},
            project_usage_deltas={},
            domain_usage_deltas={
                DomainUsageBucketKey(
                    domain_name=test_domain_name,
                    resource_group="default",
                    period_date=period,
                ): BucketDelta(slots=raw_slots, duration_seconds=duration),
            },
        )

        await db_source.increment_usage_buckets(result)

        # Verify entries were created with separated amount/duration
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
            assert slot_map["cpu"].amount == Decimal("2")
            assert slot_map["mem"].amount == Decimal("4096000")
            assert slot_map["cpu"].duration_seconds == 300
            assert slot_map["mem"].duration_seconds == 300

    @pytest.mark.asyncio
    async def test_increment_accumulates_entries(
        self,
        db_source: ResourceUsageHistoryDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> None:
        """Verify that multiple increments accumulate amount and duration."""
        period = date(2024, 1, 15)
        key = DomainUsageBucketKey(
            domain_name=test_domain_name,
            resource_group="default",
            period_date=period,
        )

        # First increment: 2 CPUs for 300 seconds
        result1 = UsageBucketAggregationResult(
            user_usage_deltas={},
            project_usage_deltas={},
            domain_usage_deltas={
                key: BucketDelta(
                    slots=ResourceSlot({"cpu": Decimal("2")}),
                    duration_seconds=300,
                ),
            },
        )
        await db_source.increment_usage_buckets(result1)

        # Second increment: 3 CPUs for 300 seconds
        result2 = UsageBucketAggregationResult(
            user_usage_deltas={},
            project_usage_deltas={},
            domain_usage_deltas={
                key: BucketDelta(
                    slots=ResourceSlot({"cpu": Decimal("3")}),
                    duration_seconds=300,
                ),
            },
        )
        await db_source.increment_usage_buckets(result2)

        # Verify accumulated: amount = 2 + 3 = 5, duration = 300 + 300 = 600
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
            assert entry_rows[0].amount == Decimal("5")
            assert entry_rows[0].duration_seconds == 600

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
        raw_slots = ResourceSlot({"cpu": Decimal("3"), "cuda.device": Decimal("2")})
        duration = 300  # 5-minute slice
        period = date(2024, 1, 15)

        result = UsageBucketAggregationResult(
            user_usage_deltas={
                UserUsageBucketKey(
                    user_uuid=user_uuid,
                    project_id=project_id,
                    domain_name=test_domain_name,
                    resource_group="default",
                    period_date=period,
                ): BucketDelta(slots=raw_slots, duration_seconds=duration),
            },
            project_usage_deltas={},
            domain_usage_deltas={},
        )

        await db_source.increment_usage_buckets(result)

        # Verify entries were created with separated amount/duration
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
            assert slot_map["cpu"].amount == Decimal("3")
            assert slot_map["cuda.device"].amount == Decimal("2")
            assert slot_map["cpu"].duration_seconds == 300

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

        # Insert two domain buckets with entries (raw amount, not resource-seconds)
        result = UsageBucketAggregationResult(
            user_usage_deltas={},
            project_usage_deltas={},
            domain_usage_deltas={
                DomainUsageBucketKey(
                    domain_name=test_domain_name,
                    resource_group="default",
                    period_date=period1,
                ): BucketDelta(
                    slots=ResourceSlot({"cpu": Decimal("2")}),
                    duration_seconds=300,
                ),
                DomainUsageBucketKey(
                    domain_name=test_domain_name,
                    resource_group="default",
                    period_date=period2,
                ): BucketDelta(
                    slots=ResourceSlot({"cpu": Decimal("3")}),
                    duration_seconds=300,
                ),
            },
        )
        await db_source.increment_usage_buckets(result)

        # Query aggregated usage — SUM(amount) across buckets
        aggregated = await db_source.get_aggregated_usage_by_domain(
            resource_group="default",
            lookback_start=date(2024, 1, 14),
            lookback_end=date(2024, 1, 17),
        )

        assert test_domain_name in aggregated
        # 2 + 3 = 5 (raw amounts summed across buckets)
        assert aggregated[test_domain_name]["cpu"] == Decimal("5")
