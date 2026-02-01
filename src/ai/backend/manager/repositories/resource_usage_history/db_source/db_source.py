"""Database source for Resource Usage History repository operations."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, cast

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult

from ai.backend.common.types import ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    Creator,
    Upserter,
    execute_batch_querier,
    execute_bulk_creator,
    execute_creator,
    execute_upserter,
)
from ai.backend.manager.repositories.resource_usage_history.types import (
    DomainUsageBucketData,
    DomainUsageBucketSearchResult,
    KernelUsageRecordData,
    KernelUsageRecordSearchResult,
    ProjectUsageBucketData,
    ProjectUsageBucketSearchResult,
    UserUsageBucketData,
    UserUsageBucketSearchResult,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
    from ai.backend.manager.sokovan.scheduler.fair_share import (
        DomainUsageBucketKey,
        ProjectUsageBucketKey,
        UsageBucketAggregationResult,
        UserUsageBucketKey,
    )

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ResourceUsageHistoryDBSource",)


class ResourceUsageHistoryDBSource:
    """Database source for Resource Usage History operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # ==================== Kernel Usage Records ====================

    async def create_kernel_usage_record(
        self,
        creator: Creator[KernelUsageRecordRow],
    ) -> KernelUsageRecordData:
        """Create a single kernel usage record."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return KernelUsageRecordData.from_row(result.row)

    async def bulk_create_kernel_usage_records(
        self,
        bulk_creator: BulkCreator[KernelUsageRecordRow],
    ) -> list[KernelUsageRecordData]:
        """Bulk create kernel usage records.

        This is the primary method used by UsageAggregationService to record
        per-period usage slices for all running kernels.
        """
        async with self._db.begin_session() as db_sess:
            result = await execute_bulk_creator(db_sess, bulk_creator)
            return [KernelUsageRecordData.from_row(row) for row in result.rows]

    async def bulk_create_kernel_usage_records_with_observation_update(
        self,
        bulk_creator: BulkCreator[KernelUsageRecordRow],
        kernel_observation_times: Mapping[uuid.UUID, datetime],
    ) -> tuple[list[KernelUsageRecordData], int]:
        """Bulk create kernel usage records and update observation timestamps atomically.

        This method performs both operations in a single transaction for data consistency:
        1. Bulk create kernel usage records
        2. Update last_observed_at for the observed kernels

        Args:
            bulk_creator: Specs for creating kernel usage records
            kernel_observation_times: Mapping of kernel ID to observation timestamp

        Returns:
            Tuple of (created records data, number of kernels with updated observation times)
        """
        async with self._db.begin_session() as db_sess:
            # Step 1: Bulk create kernel usage records
            result = await execute_bulk_creator(db_sess, bulk_creator)
            records = [KernelUsageRecordData.from_row(row) for row in result.rows]

            # Step 2: Update last_observed_at for kernels
            updated_count = 0
            if kernel_observation_times:
                # Group by observation time for efficient batch updates
                time_to_kernels: dict[datetime, list[uuid.UUID]] = {}
                for kernel_id, observed_at in kernel_observation_times.items():
                    time_to_kernels.setdefault(observed_at, []).append(kernel_id)

                for observed_at, kernel_ids in time_to_kernels.items():
                    update_stmt = (
                        sa.update(KernelRow)
                        .where(KernelRow.id.in_(kernel_ids))
                        .values(last_observed_at=observed_at)
                    )
                    update_result = await db_sess.execute(update_stmt)
                    updated_count += cast(CursorResult[Any], update_result).rowcount

            return records, updated_count

    async def record_fair_share_observation(
        self,
        bulk_creator: BulkCreator[KernelUsageRecordRow],
        kernel_observation_times: Mapping[uuid.UUID, datetime],
        aggregation_result: UsageBucketAggregationResult,
        decay_unit_days: int = 1,
    ) -> tuple[list[KernelUsageRecordData], int]:
        """Record fair share observation data atomically.

        This method combines all fair share observation writes in a single transaction:
        1. Bulk create kernel usage records
        2. Update last_observed_at for the observed kernels
        3. Increment user/project/domain usage buckets

        By performing all writes in a single transaction, we ensure data consistency
        even if the server crashes mid-operation.

        Args:
            bulk_creator: Specs for creating kernel usage records
            kernel_observation_times: Mapping of kernel ID to observation timestamp
            aggregation_result: Aggregated usage deltas for bucket updates
            decay_unit_days: Decay unit days for new buckets (default: 1)

        Returns:
            Tuple of (created records data, number of kernels with updated observation times)
        """
        log.debug(
            "[DBSource] record_fair_share_observation: specs_count={}, "
            "kernel_observation_times_count={}, user_deltas={}, project_deltas={}, "
            "domain_deltas={}",
            len(bulk_creator.specs),
            len(kernel_observation_times),
            len(aggregation_result.user_usage_deltas),
            len(aggregation_result.project_usage_deltas),
            len(aggregation_result.domain_usage_deltas),
        )

        async with self._db.begin_session() as db_sess:
            # Step 1: Bulk create kernel usage records
            result = await execute_bulk_creator(db_sess, bulk_creator)
            records = [KernelUsageRecordData.from_row(row) for row in result.rows]

            log.debug("[DBSource] Created {} kernel usage records", len(records))

            # Step 2: Update last_observed_at for kernels
            updated_count = 0
            if kernel_observation_times:
                time_to_kernels: dict[datetime, list[uuid.UUID]] = {}
                for kernel_id, observed_at in kernel_observation_times.items():
                    time_to_kernels.setdefault(observed_at, []).append(kernel_id)

                for observed_at, kernel_ids in time_to_kernels.items():
                    update_stmt = (
                        sa.update(KernelRow)
                        .where(KernelRow.id.in_(kernel_ids))
                        .values(last_observed_at=observed_at)
                    )
                    update_result = await db_sess.execute(update_stmt)
                    updated_count += cast(CursorResult[Any], update_result).rowcount

            log.debug("[DBSource] Updated last_observed_at for {} kernels", updated_count)

            # Step 3: Increment usage buckets
            await self._increment_user_usage_buckets(
                db_sess, aggregation_result.user_usage_deltas, decay_unit_days
            )
            await self._increment_project_usage_buckets(
                db_sess, aggregation_result.project_usage_deltas, decay_unit_days
            )
            await self._increment_domain_usage_buckets(
                db_sess, aggregation_result.domain_usage_deltas, decay_unit_days
            )

            log.debug("[DBSource] Incremented usage buckets successfully")

            return records, updated_count

    async def search_kernel_usage_records(
        self,
        querier: BatchQuerier,
    ) -> KernelUsageRecordSearchResult:
        """Search kernel usage records with pagination."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(KernelUsageRecordRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [
                KernelUsageRecordData.from_row(row.KernelUsageRecordRow) for row in result.rows
            ]
            return KernelUsageRecordSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ==================== Domain Usage Buckets ====================

    async def create_domain_usage_bucket(
        self,
        creator: Creator[DomainUsageBucketRow],
    ) -> DomainUsageBucketData:
        """Create a new domain usage bucket."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return DomainUsageBucketData.from_row(result.row)

    async def upsert_domain_usage_bucket(
        self,
        upserter: Upserter[DomainUsageBucketRow],
    ) -> DomainUsageBucketData:
        """Upsert a domain usage bucket."""
        async with self._db.begin_session() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["domain_name", "resource_group", "period_start"],
            )
            return DomainUsageBucketData.from_row(result.row)

    async def search_domain_usage_buckets(
        self,
        querier: BatchQuerier,
    ) -> DomainUsageBucketSearchResult:
        """Search domain usage buckets with pagination."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(DomainUsageBucketRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [
                DomainUsageBucketData.from_row(row.DomainUsageBucketRow) for row in result.rows
            ]
            return DomainUsageBucketSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ==================== Project Usage Buckets ====================

    async def create_project_usage_bucket(
        self,
        creator: Creator[ProjectUsageBucketRow],
    ) -> ProjectUsageBucketData:
        """Create a new project usage bucket."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return ProjectUsageBucketData.from_row(result.row)

    async def upsert_project_usage_bucket(
        self,
        upserter: Upserter[ProjectUsageBucketRow],
    ) -> ProjectUsageBucketData:
        """Upsert a project usage bucket."""
        async with self._db.begin_session() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["project_id", "resource_group", "period_start"],
            )
            return ProjectUsageBucketData.from_row(result.row)

    async def search_project_usage_buckets(
        self,
        querier: BatchQuerier,
    ) -> ProjectUsageBucketSearchResult:
        """Search project usage buckets with pagination."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ProjectUsageBucketRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [
                ProjectUsageBucketData.from_row(row.ProjectUsageBucketRow) for row in result.rows
            ]
            return ProjectUsageBucketSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ==================== User Usage Buckets ====================

    async def create_user_usage_bucket(
        self,
        creator: Creator[UserUsageBucketRow],
    ) -> UserUsageBucketData:
        """Create a new user usage bucket."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return UserUsageBucketData.from_row(result.row)

    async def upsert_user_usage_bucket(
        self,
        upserter: Upserter[UserUsageBucketRow],
    ) -> UserUsageBucketData:
        """Upsert a user usage bucket."""
        async with self._db.begin_session() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["user_uuid", "project_id", "resource_group", "period_start"],
            )
            return UserUsageBucketData.from_row(result.row)

    async def search_user_usage_buckets(
        self,
        querier: BatchQuerier,
    ) -> UserUsageBucketSearchResult:
        """Search user usage buckets with pagination."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(UserUsageBucketRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [UserUsageBucketData.from_row(row.UserUsageBucketRow) for row in result.rows]
            return UserUsageBucketSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ==================== Aggregation Queries ====================

    async def get_aggregated_usage_by_user(
        self,
        resource_group: str,
        lookback_start: date,
        lookback_end: date,
    ) -> Mapping[tuple[uuid.UUID, uuid.UUID], ResourceSlot]:
        """Get aggregated usage by (user_uuid, project_id) pairs.

        This method aggregates resource_usage across all buckets within the
        lookback period for each user-project pair.

        Note: ResourceSlot is a JSONB type and cannot be aggregated in SQL,
        so we fetch all rows and aggregate in Python.
        """
        async with self._db.begin_readonly_session() as db_sess:
            return await self._fetch_aggregated_usage_by_user(
                db_sess, resource_group, lookback_start, lookback_end
            )

    async def _fetch_aggregated_usage_by_user(
        self,
        db_sess: SASession,
        resource_group: str,
        lookback_start: date,
        lookback_end: date,
    ) -> Mapping[tuple[uuid.UUID, uuid.UUID], ResourceSlot]:
        """Private method to fetch and aggregate user usage."""
        query = sa.select(
            UserUsageBucketRow.user_uuid,
            UserUsageBucketRow.project_id,
            UserUsageBucketRow.resource_usage,
        ).where(
            sa.and_(
                UserUsageBucketRow.resource_group == resource_group,
                UserUsageBucketRow.period_start >= lookback_start,
                UserUsageBucketRow.period_start <= lookback_end,
            )
        )
        result = await db_sess.execute(query)
        rows = result.all()

        # Aggregate in Python since ResourceSlot is JSONB
        aggregated: dict[tuple[uuid.UUID, uuid.UUID], ResourceSlot] = {}
        for row in rows:
            key = (row.user_uuid, row.project_id)
            if key not in aggregated:
                aggregated[key] = ResourceSlot()
            aggregated[key] = aggregated[key] + row.resource_usage
        return aggregated

    async def get_aggregated_usage_by_project(
        self,
        resource_group: str,
        lookback_start: date,
        lookback_end: date,
    ) -> Mapping[uuid.UUID, ResourceSlot]:
        """Get aggregated usage by project_id.

        This method aggregates resource_usage across all buckets within the
        lookback period for each project.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(
                ProjectUsageBucketRow.project_id,
                ProjectUsageBucketRow.resource_usage,
            ).where(
                sa.and_(
                    ProjectUsageBucketRow.resource_group == resource_group,
                    ProjectUsageBucketRow.period_start >= lookback_start,
                    ProjectUsageBucketRow.period_start <= lookback_end,
                )
            )
            result = await db_sess.execute(query)
            rows = result.all()

            # Aggregate in Python since ResourceSlot is JSONB
            aggregated: dict[uuid.UUID, ResourceSlot] = {}
            for row in rows:
                if row.project_id not in aggregated:
                    aggregated[row.project_id] = ResourceSlot()
                aggregated[row.project_id] = aggregated[row.project_id] + row.resource_usage
            return aggregated

    async def get_aggregated_usage_by_domain(
        self,
        resource_group: str,
        lookback_start: date,
        lookback_end: date,
    ) -> Mapping[str, ResourceSlot]:
        """Get aggregated usage by domain_name.

        This method aggregates resource_usage across all buckets within the
        lookback period for each domain.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(
                DomainUsageBucketRow.domain_name,
                DomainUsageBucketRow.resource_usage,
            ).where(
                sa.and_(
                    DomainUsageBucketRow.resource_group == resource_group,
                    DomainUsageBucketRow.period_start >= lookback_start,
                    DomainUsageBucketRow.period_start <= lookback_end,
                )
            )
            result = await db_sess.execute(query)
            rows = result.all()

            # Aggregate in Python since ResourceSlot is JSONB
            aggregated: dict[str, ResourceSlot] = {}
            for row in rows:
                if row.domain_name not in aggregated:
                    aggregated[row.domain_name] = ResourceSlot()
                aggregated[row.domain_name] = aggregated[row.domain_name] + row.resource_usage
            return aggregated

    # ==================== Bucket Delta Updates ====================

    async def increment_usage_buckets(
        self,
        aggregation_result: UsageBucketAggregationResult,
        decay_unit_days: int = 1,
    ) -> None:
        """Increment usage buckets with aggregated deltas.

        For each bucket key:
        - If bucket exists: add delta to existing resource_usage
        - If bucket doesn't exist: create new bucket with delta as resource_usage

        All operations are performed in a single transaction for consistency.

        Args:
            aggregation_result: Aggregated usage deltas from FairShareAggregator
            decay_unit_days: Decay unit days for new buckets (default: 1)
        """
        if not (
            aggregation_result.user_usage_deltas
            or aggregation_result.project_usage_deltas
            or aggregation_result.domain_usage_deltas
        ):
            return

        async with self._db.begin_session() as db_sess:
            # Process user buckets
            await self._increment_user_usage_buckets(
                db_sess, aggregation_result.user_usage_deltas, decay_unit_days
            )

            # Process project buckets
            await self._increment_project_usage_buckets(
                db_sess, aggregation_result.project_usage_deltas, decay_unit_days
            )

            # Process domain buckets
            await self._increment_domain_usage_buckets(
                db_sess, aggregation_result.domain_usage_deltas, decay_unit_days
            )

    async def _increment_user_usage_buckets(
        self,
        db_sess: SASession,
        deltas: Mapping[UserUsageBucketKey, ResourceSlot],
        decay_unit_days: int,
    ) -> None:
        """Increment user usage buckets with deltas."""
        if not deltas:
            return

        # Fetch existing buckets
        keys_list = list(deltas.keys())
        existing = await self._fetch_existing_user_buckets(db_sess, keys_list)

        for key, delta in deltas.items():
            lookup_key = (key.user_uuid, key.project_id, key.resource_group, key.period_date)
            existing_usage = existing.get(lookup_key, ResourceSlot())
            new_usage = existing_usage + delta

            # Upsert with merged usage
            stmt = (
                pg_insert(UserUsageBucketRow.__table__)
                .values(
                    user_uuid=key.user_uuid,
                    project_id=key.project_id,
                    domain_name=key.domain_name,
                    resource_group=key.resource_group,
                    period_start=key.period_date,
                    period_end=key.period_date,
                    decay_unit_days=decay_unit_days,
                    resource_usage=new_usage,
                )
                .on_conflict_do_update(
                    index_elements=["user_uuid", "project_id", "resource_group", "period_start"],
                    set_={"resource_usage": new_usage, "updated_at": sa.func.now()},
                )
            )
            await db_sess.execute(stmt)

    async def _fetch_existing_user_buckets(
        self,
        db_sess: SASession,
        keys: list[UserUsageBucketKey],
    ) -> dict[tuple[uuid.UUID, uuid.UUID, str, date], ResourceSlot]:
        """Fetch existing user buckets for the given keys."""
        if not keys:
            return {}

        # Build OR conditions for each key
        conditions = [
            sa.and_(
                UserUsageBucketRow.user_uuid == key.user_uuid,
                UserUsageBucketRow.project_id == key.project_id,
                UserUsageBucketRow.resource_group == key.resource_group,
                UserUsageBucketRow.period_start == key.period_date,
            )
            for key in keys
        ]

        query = sa.select(
            UserUsageBucketRow.user_uuid,
            UserUsageBucketRow.project_id,
            UserUsageBucketRow.resource_group,
            UserUsageBucketRow.period_start,
            UserUsageBucketRow.resource_usage,
        ).where(sa.or_(*conditions))

        result = await db_sess.execute(query)
        return {
            (
                row.user_uuid,
                row.project_id,
                row.resource_group,
                row.period_start,
            ): row.resource_usage
            for row in result.all()
        }

    async def _increment_project_usage_buckets(
        self,
        db_sess: SASession,
        deltas: Mapping[ProjectUsageBucketKey, ResourceSlot],
        decay_unit_days: int,
    ) -> None:
        """Increment project usage buckets with deltas."""
        if not deltas:
            return

        # Fetch existing buckets
        keys_list = list(deltas.keys())
        existing = await self._fetch_existing_project_buckets(db_sess, keys_list)

        for key, delta in deltas.items():
            lookup_key = (key.project_id, key.resource_group, key.period_date)
            existing_usage = existing.get(lookup_key, ResourceSlot())
            new_usage = existing_usage + delta

            # Upsert with merged usage
            stmt = (
                pg_insert(ProjectUsageBucketRow.__table__)
                .values(
                    project_id=key.project_id,
                    domain_name=key.domain_name,
                    resource_group=key.resource_group,
                    period_start=key.period_date,
                    period_end=key.period_date,
                    decay_unit_days=decay_unit_days,
                    resource_usage=new_usage,
                )
                .on_conflict_do_update(
                    index_elements=["project_id", "resource_group", "period_start"],
                    set_={"resource_usage": new_usage, "updated_at": sa.func.now()},
                )
            )
            await db_sess.execute(stmt)

    async def _fetch_existing_project_buckets(
        self,
        db_sess: SASession,
        keys: list[ProjectUsageBucketKey],
    ) -> dict[tuple[uuid.UUID, str, date], ResourceSlot]:
        """Fetch existing project buckets for the given keys."""
        if not keys:
            return {}

        conditions = [
            sa.and_(
                ProjectUsageBucketRow.project_id == key.project_id,
                ProjectUsageBucketRow.resource_group == key.resource_group,
                ProjectUsageBucketRow.period_start == key.period_date,
            )
            for key in keys
        ]

        query = sa.select(
            ProjectUsageBucketRow.project_id,
            ProjectUsageBucketRow.resource_group,
            ProjectUsageBucketRow.period_start,
            ProjectUsageBucketRow.resource_usage,
        ).where(sa.or_(*conditions))

        result = await db_sess.execute(query)
        return {
            (row.project_id, row.resource_group, row.period_start): row.resource_usage
            for row in result.all()
        }

    async def _increment_domain_usage_buckets(
        self,
        db_sess: SASession,
        deltas: Mapping[DomainUsageBucketKey, ResourceSlot],
        decay_unit_days: int,
    ) -> None:
        """Increment domain usage buckets with deltas."""
        if not deltas:
            return

        # Fetch existing buckets
        keys_list = list(deltas.keys())
        existing = await self._fetch_existing_domain_buckets(db_sess, keys_list)

        for key, delta in deltas.items():
            lookup_key = (key.domain_name, key.resource_group, key.period_date)
            existing_usage = existing.get(lookup_key, ResourceSlot())
            new_usage = existing_usage + delta

            # Upsert with merged usage
            stmt = (
                pg_insert(DomainUsageBucketRow.__table__)
                .values(
                    domain_name=key.domain_name,
                    resource_group=key.resource_group,
                    period_start=key.period_date,
                    period_end=key.period_date,
                    decay_unit_days=decay_unit_days,
                    resource_usage=new_usage,
                )
                .on_conflict_do_update(
                    index_elements=["domain_name", "resource_group", "period_start"],
                    set_={"resource_usage": new_usage, "updated_at": sa.func.now()},
                )
            )
            await db_sess.execute(stmt)

    async def _fetch_existing_domain_buckets(
        self,
        db_sess: SASession,
        keys: list[DomainUsageBucketKey],
    ) -> dict[tuple[str, str, date], ResourceSlot]:
        """Fetch existing domain buckets for the given keys."""
        if not keys:
            return {}

        conditions = [
            sa.and_(
                DomainUsageBucketRow.domain_name == key.domain_name,
                DomainUsageBucketRow.resource_group == key.resource_group,
                DomainUsageBucketRow.period_start == key.period_date,
            )
            for key in keys
        ]

        query = sa.select(
            DomainUsageBucketRow.domain_name,
            DomainUsageBucketRow.resource_group,
            DomainUsageBucketRow.period_start,
            DomainUsageBucketRow.resource_usage,
        ).where(sa.or_(*conditions))

        result = await db_sess.execute(query)
        return {
            (row.domain_name, row.resource_group, row.period_start): row.resource_usage
            for row in result.all()
        }
