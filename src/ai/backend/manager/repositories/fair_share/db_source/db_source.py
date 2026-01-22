"""Database source for Fair Share repository operations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, timedelta
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    DomainFairShareSearchResult,
    FairShareCalculationContext,
    FairSharesByLevel,
    ProjectFairShareData,
    ProjectFairShareSearchResult,
    ProjectUserIds,
    RawUsageBucketsByLevel,
    UserFairShareData,
    UserFairShareFactors,
    UserFairShareSearchResult,
    UserProjectKey,
)
from ai.backend.manager.errors.fair_share import FairShareNotFoundError
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    Upserter,
    execute_batch_querier,
    execute_creator,
    execute_upserter,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
    from ai.backend.manager.sokovan.scheduler.fair_share import FairShareFactorCalculationResult


__all__ = ("FairShareDBSource",)


class FairShareDBSource:
    """Database source for Fair Share operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # ==================== Domain Fair Share ====================

    async def create_domain_fair_share(
        self,
        creator: Creator[DomainFairShareRow],
    ) -> DomainFairShareData:
        """Create a new domain fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    async def upsert_domain_fair_share(
        self,
        upserter: Upserter[DomainFairShareRow],
    ) -> DomainFairShareData:
        """Upsert a domain fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["resource_group", "domain_name"],
            )
            return result.row.to_data()

    async def get_domain_fair_share(
        self,
        resource_group: str,
        domain_name: str,
    ) -> DomainFairShareData:
        """Get a domain fair share record by scaling group and domain name.

        Raises:
            FairShareNotFoundError: If the domain fair share is not found.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DomainFairShareRow).where(
                sa.and_(
                    DomainFairShareRow.resource_group == resource_group,
                    DomainFairShareRow.domain_name == domain_name,
                )
            )
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise FairShareNotFoundError(
                    f"Domain fair share not found: resource_group={resource_group}, domain_name={domain_name}"
                )
            return row.to_data()

    async def search_domain_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> DomainFairShareSearchResult:
        """Search domain fair shares with pagination."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DomainFairShareRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.DomainFairShareRow.to_data() for row in result.rows]
            return DomainFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ==================== Project Fair Share ====================

    async def create_project_fair_share(
        self,
        creator: Creator[ProjectFairShareRow],
    ) -> ProjectFairShareData:
        """Create a new project fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    async def upsert_project_fair_share(
        self,
        upserter: Upserter[ProjectFairShareRow],
    ) -> ProjectFairShareData:
        """Upsert a project fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["resource_group", "project_id"],
            )
            return result.row.to_data()

    async def get_project_fair_share(
        self,
        resource_group: str,
        project_id: uuid.UUID,
    ) -> ProjectFairShareData:
        """Get a project fair share record by scaling group and project ID.

        Raises:
            FairShareNotFoundError: If the project fair share is not found.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ProjectFairShareRow).where(
                sa.and_(
                    ProjectFairShareRow.resource_group == resource_group,
                    ProjectFairShareRow.project_id == project_id,
                )
            )
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise FairShareNotFoundError(
                    f"Project fair share not found: resource_group={resource_group}, project_id={project_id}"
                )
            return row.to_data()

    async def search_project_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> ProjectFairShareSearchResult:
        """Search project fair shares with pagination."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ProjectFairShareRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.ProjectFairShareRow.to_data() for row in result.rows]
            return ProjectFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ==================== User Fair Share ====================

    async def create_user_fair_share(
        self,
        creator: Creator[UserFairShareRow],
    ) -> UserFairShareData:
        """Create a new user fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    async def upsert_user_fair_share(
        self,
        upserter: Upserter[UserFairShareRow],
    ) -> UserFairShareData:
        """Upsert a user fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["resource_group", "user_uuid", "project_id"],
            )
            return result.row.to_data()

    async def get_user_fair_share(
        self,
        resource_group: str,
        project_id: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> UserFairShareData:
        """Get a user fair share record by scaling group, project ID, and user UUID.

        Raises:
            FairShareNotFoundError: If the user fair share is not found.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(UserFairShareRow).where(
                sa.and_(
                    UserFairShareRow.resource_group == resource_group,
                    UserFairShareRow.project_id == project_id,
                    UserFairShareRow.user_uuid == user_uuid,
                )
            )
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise FairShareNotFoundError(
                    f"User fair share not found: resource_group={resource_group}, "
                    f"project_id={project_id}, user_uuid={user_uuid}"
                )
            return row.to_data()

    async def search_user_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> UserFairShareSearchResult:
        """Search user fair shares with pagination."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(UserFairShareRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.UserFairShareRow.to_data() for row in result.rows]
            return UserFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def get_user_scheduling_ranks_batch(
        self,
        resource_group: str,
        project_user_ids: Sequence[ProjectUserIds],
    ) -> dict[uuid.UUID, int]:
        """Get scheduling ranks for multiple users across projects.

        Args:
            resource_group: The resource group (scaling group) name.
            project_user_ids: Sequence of ProjectUserIds containing project and user IDs.

        Returns:
            A mapping from user_uuid to scheduling_rank.
            Users not found in the database or with NULL rank are omitted.
        """
        if not project_user_ids:
            return {}

        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Build OR conditions for each project-users group
            conditions = [
                sa.and_(
                    UserFairShareRow.project_id == pu.project_id,
                    UserFairShareRow.user_uuid.in_(pu.user_ids),
                )
                for pu in project_user_ids
                if pu.user_ids
            ]

            if not conditions:
                return {}

            query = sa.select(
                UserFairShareRow.user_uuid,
                UserFairShareRow.scheduling_rank,
            ).where(
                sa.and_(
                    UserFairShareRow.resource_group == resource_group,
                    UserFairShareRow.scheduling_rank.is_not(None),
                    sa.or_(*conditions),
                )
            )

            result = await db_sess.execute(query)
            return {row.user_uuid: row.scheduling_rank for row in result}

    # ==================== Bulk Factor Updates ====================

    async def bulk_update_fair_share_factors(
        self,
        resource_group: str,
        calculation_result: FairShareFactorCalculationResult,
        lookback_start: date,
        lookback_end: date,
    ) -> None:
        """Bulk update fair share factors and scheduling ranks for all levels.

        Updates domain, project, and user fair share records with calculated
        factors and ranks in a single transaction.

        Args:
            resource_group: The resource group being updated
            calculation_result: Calculated factors and ranks from FairShareFactorCalculator
            lookback_start: Start of lookback period used in calculation
            lookback_end: End of lookback period used in calculation
        """
        # Build rank lookup for O(1) access
        rank_by_user: dict[UserProjectKey, int] = {
            UserProjectKey(rank.user_uuid, rank.project_id): rank.rank
            for rank in calculation_result.scheduling_ranks
        }

        async with self._db.begin_session() as db_sess:
            now = sa.func.now()

            # Update domain fair shares
            for domain_name, domain_result in calculation_result.domain_results.items():
                await db_sess.execute(
                    sa.update(DomainFairShareRow)
                    .where(
                        sa.and_(
                            DomainFairShareRow.resource_group == resource_group,
                            DomainFairShareRow.domain_name == domain_name,
                        )
                    )
                    .values(
                        fair_share_factor=domain_result.fair_share_factor,
                        total_decayed_usage=domain_result.total_decayed_usage,
                        normalized_usage=domain_result.normalized_usage,
                        lookback_start=lookback_start,
                        lookback_end=lookback_end,
                        last_calculated_at=now,
                    )
                )

            # Update project fair shares
            for project_id, project_result in calculation_result.project_results.items():
                await db_sess.execute(
                    sa.update(ProjectFairShareRow)
                    .where(
                        sa.and_(
                            ProjectFairShareRow.resource_group == resource_group,
                            ProjectFairShareRow.project_id == project_id,
                        )
                    )
                    .values(
                        fair_share_factor=project_result.fair_share_factor,
                        total_decayed_usage=project_result.total_decayed_usage,
                        normalized_usage=project_result.normalized_usage,
                        lookback_start=lookback_start,
                        lookback_end=lookback_end,
                        last_calculated_at=now,
                    )
                )

            # Update user fair shares with scheduling ranks
            for user_key, user_result in calculation_result.user_results.items():
                scheduling_rank = rank_by_user.get(user_key)
                await db_sess.execute(
                    sa.update(UserFairShareRow)
                    .where(
                        sa.and_(
                            UserFairShareRow.resource_group == resource_group,
                            UserFairShareRow.user_uuid == user_key.user_uuid,
                            UserFairShareRow.project_id == user_key.project_id,
                        )
                    )
                    .values(
                        fair_share_factor=user_result.fair_share_factor,
                        total_decayed_usage=user_result.total_decayed_usage,
                        normalized_usage=user_result.normalized_usage,
                        lookback_start=lookback_start,
                        lookback_end=lookback_end,
                        last_calculated_at=now,
                        scheduling_rank=scheduling_rank,
                    )
                )

    # ==================== Batched Reads ====================

    async def get_user_fair_share_factors_batch(
        self,
        resource_group: str,
        project_user_ids: Sequence[ProjectUserIds],
    ) -> dict[uuid.UUID, UserFairShareFactors]:
        """Get combined fair share factors for multiple users with 3-way JOIN.

        Fetches domain, project, and user fair share factors in a single query
        by joining the three fair share tables.

        Args:
            resource_group: The resource group (scaling group) name.
            project_user_ids: Sequence of ProjectUserIds containing project and user IDs.

        Returns:
            A mapping from user_uuid to UserFairShareFactors containing all three factor levels.
            Users not found in any of the fair share tables are omitted.
        """
        if not project_user_ids:
            return {}

        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Build OR conditions for each project-users group
            conditions = [
                sa.and_(
                    UserFairShareRow.project_id == pu.project_id,
                    UserFairShareRow.user_uuid.in_(pu.user_ids),
                )
                for pu in project_user_ids
                if pu.user_ids
            ]

            if not conditions:
                return {}

            # 3-way JOIN query: user -> project -> domain
            query = (
                sa.select(
                    UserFairShareRow.user_uuid,
                    UserFairShareRow.project_id,
                    UserFairShareRow.domain_name,
                    UserFairShareRow.fair_share_factor.label("user_factor"),
                    ProjectFairShareRow.fair_share_factor.label("project_factor"),
                    DomainFairShareRow.fair_share_factor.label("domain_factor"),
                )
                .select_from(UserFairShareRow)
                .join(
                    ProjectFairShareRow,
                    sa.and_(
                        ProjectFairShareRow.resource_group == UserFairShareRow.resource_group,
                        ProjectFairShareRow.project_id == UserFairShareRow.project_id,
                    ),
                )
                .join(
                    DomainFairShareRow,
                    sa.and_(
                        DomainFairShareRow.resource_group == UserFairShareRow.resource_group,
                        DomainFairShareRow.domain_name == UserFairShareRow.domain_name,
                    ),
                )
                .where(
                    sa.and_(
                        UserFairShareRow.resource_group == resource_group,
                        sa.or_(*conditions),
                    )
                )
            )

            result = await db_sess.execute(query)
            return {
                row.user_uuid: UserFairShareFactors(
                    user_uuid=row.user_uuid,
                    project_id=row.project_id,
                    domain_name=row.domain_name,
                    domain_factor=row.domain_factor,
                    project_factor=row.project_factor,
                    user_factor=row.user_factor,
                )
                for row in result
            }

    async def get_fair_share_calculation_context(
        self,
        scaling_group: str,
        today: date,
    ) -> FairShareCalculationContext:
        """Get all data needed for fair share factor calculation in a single session.

        Fetches scaling group config, fair share records, and raw usage buckets
        in one database session for consistency and efficiency.

        The Calculator is responsible for applying time decay to raw usage buckets.

        Args:
            scaling_group: The scaling group name
            today: Current date for decay calculation

        Returns:
            FairShareCalculationContext containing all data for factor calculation

        Raises:
            ScalingGroupNotFound: If the scaling group doesn't exist
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # 1. Fetch scaling group spec
            spec = await self._fetch_fair_share_spec(db_sess, scaling_group)

            # Calculate lookback range
            lookback_start = today - timedelta(days=spec.lookback_days)
            lookback_end = today

            # 2. Fetch fair shares
            fair_shares = await self._fetch_fair_shares(db_sess, scaling_group)

            # 3. Fetch raw usage buckets (no decay applied)
            raw_usage_buckets = await self._fetch_raw_usage_buckets(
                db_sess, scaling_group, lookback_start, lookback_end
            )

        return FairShareCalculationContext(
            fair_shares=fair_shares,
            raw_usage_buckets=raw_usage_buckets,
            half_life_days=spec.half_life_days,
            lookback_days=spec.lookback_days,
            default_weight=spec.default_weight,
            resource_weights=spec.resource_weights,
            today=today,
        )

    async def _fetch_fair_share_spec(
        self,
        db_sess: SASession,
        scaling_group: str,
    ) -> FairShareScalingGroupSpec:
        """Fetch fair share spec from scaling group."""
        result = await db_sess.execute(
            sa.select(
                ScalingGroupRow.name,
                ScalingGroupRow.fair_share_spec,
            ).where(ScalingGroupRow.name == scaling_group)
        )
        row = result.one_or_none()
        if row is None:
            raise ScalingGroupNotFound(scaling_group)

        if row.fair_share_spec is not None:
            return row.fair_share_spec

        return FairShareScalingGroupSpec()

    async def _fetch_fair_shares(
        self,
        db_sess: SASession,
        scaling_group: str,
    ) -> FairSharesByLevel:
        """Fetch all fair share records for a resource group."""
        # Get domain fair shares
        domain_query = sa.select(DomainFairShareRow).where(
            DomainFairShareRow.resource_group == scaling_group
        )
        domain_result = await db_sess.execute(domain_query)
        domain_fair_shares = {row.domain_name: row.to_data() for row in domain_result.scalars()}

        # Get project fair shares
        project_query = sa.select(ProjectFairShareRow).where(
            ProjectFairShareRow.resource_group == scaling_group
        )
        project_result = await db_sess.execute(project_query)
        project_fair_shares = {row.project_id: row.to_data() for row in project_result.scalars()}

        # Get user fair shares
        user_query = sa.select(UserFairShareRow).where(
            UserFairShareRow.resource_group == scaling_group
        )
        user_result = await db_sess.execute(user_query)
        user_fair_shares = {
            UserProjectKey(row.user_uuid, row.project_id): row.to_data()
            for row in user_result.scalars()
        }

        return FairSharesByLevel(
            domain=domain_fair_shares,
            project=project_fair_shares,
            user=user_fair_shares,
        )

    async def _fetch_raw_usage_buckets(
        self,
        db_sess: SASession,
        scaling_group: str,
        lookback_start: date,
        lookback_end: date,
    ) -> RawUsageBucketsByLevel:
        """Fetch raw usage buckets without applying decay.

        Returns per-date buckets for each entity. The Calculator is responsible
        for applying time decay to these raw values.
        """
        # Fetch user usage buckets
        user_query = sa.select(
            UserUsageBucketRow.user_uuid,
            UserUsageBucketRow.project_id,
            UserUsageBucketRow.period_start,
            UserUsageBucketRow.resource_usage,
        ).where(
            sa.and_(
                UserUsageBucketRow.resource_group == scaling_group,
                UserUsageBucketRow.period_start >= lookback_start,
                UserUsageBucketRow.period_start <= lookback_end,
            )
        )
        user_result = await db_sess.execute(user_query)
        user_rows = user_result.all()

        # Fetch project usage buckets
        project_query = sa.select(
            ProjectUsageBucketRow.project_id,
            ProjectUsageBucketRow.period_start,
            ProjectUsageBucketRow.resource_usage,
        ).where(
            sa.and_(
                ProjectUsageBucketRow.resource_group == scaling_group,
                ProjectUsageBucketRow.period_start >= lookback_start,
                ProjectUsageBucketRow.period_start <= lookback_end,
            )
        )
        project_result = await db_sess.execute(project_query)
        project_rows = project_result.all()

        # Fetch domain usage buckets
        domain_query = sa.select(
            DomainUsageBucketRow.domain_name,
            DomainUsageBucketRow.period_start,
            DomainUsageBucketRow.resource_usage,
        ).where(
            sa.and_(
                DomainUsageBucketRow.resource_group == scaling_group,
                DomainUsageBucketRow.period_start >= lookback_start,
                DomainUsageBucketRow.period_start <= lookback_end,
            )
        )
        domain_result = await db_sess.execute(domain_query)
        domain_rows = domain_result.all()

        # Organize into per-date buckets (no decay applied)
        user_buckets: dict[UserProjectKey, dict[date, ResourceSlot]] = {}
        for user_row in user_rows:
            key = UserProjectKey(user_row.user_uuid, user_row.project_id)
            if key not in user_buckets:
                user_buckets[key] = {}
            user_buckets[key][user_row.period_start] = user_row.resource_usage

        project_buckets: dict[uuid.UUID, dict[date, ResourceSlot]] = {}
        for project_row in project_rows:
            if project_row.project_id not in project_buckets:
                project_buckets[project_row.project_id] = {}
            project_buckets[project_row.project_id][project_row.period_start] = (
                project_row.resource_usage
            )

        domain_buckets: dict[str, dict[date, ResourceSlot]] = {}
        for domain_row in domain_rows:
            if domain_row.domain_name not in domain_buckets:
                domain_buckets[domain_row.domain_name] = {}
            domain_buckets[domain_row.domain_name][domain_row.period_start] = (
                domain_row.resource_usage
            )

        return RawUsageBucketsByLevel(
            domain=domain_buckets,
            project=project_buckets,
            user=user_buckets,
        )
