"""Database source for Fair Share repository operations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    DomainFairShareSearchResult,
    ProjectFairShareData,
    ProjectFairShareSearchResult,
    ProjectUserIds,
    UserFairShareData,
    UserFairShareSearchResult,
)
from ai.backend.manager.errors.fair_share import FairShareNotFoundError
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    Upserter,
    execute_batch_querier,
    execute_creator,
    execute_upserter,
)

if TYPE_CHECKING:
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
        """Bulk update fair share factors for all levels.

        Updates domain, project, and user fair share records with calculated
        factors in a single transaction.

        Args:
            resource_group: The resource group being updated
            calculation_result: Calculated factors from FairShareFactorCalculator
            lookback_start: Start of lookback period used in calculation
            lookback_end: End of lookback period used in calculation
        """
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

            # Update user fair shares
            for (user_uuid, project_id), user_result in calculation_result.user_results.items():
                await db_sess.execute(
                    sa.update(UserFairShareRow)
                    .where(
                        sa.and_(
                            UserFairShareRow.resource_group == resource_group,
                            UserFairShareRow.user_uuid == user_uuid,
                            UserFairShareRow.project_id == project_id,
                        )
                    )
                    .values(
                        fair_share_factor=user_result.fair_share_factor,
                        total_decayed_usage=user_result.total_decayed_usage,
                        normalized_usage=user_result.normalized_usage,
                        lookback_start=lookback_start,
                        lookback_end=lookback_end,
                        last_calculated_at=now,
                    )
                )

    async def get_all_fair_shares_for_resource_group(
        self,
        resource_group: str,
    ) -> tuple[
        dict[str, DomainFairShareData],
        dict[uuid.UUID, ProjectFairShareData],
        dict[tuple[uuid.UUID, uuid.UUID], UserFairShareData],
    ]:
        """Get all fair share records for a resource group.

        Used for factor calculation to get current weights and configurations.

        Args:
            resource_group: The resource group to query

        Returns:
            Tuple of (domain_fair_shares, project_fair_shares, user_fair_shares)
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Get domain fair shares
            domain_query = sa.select(DomainFairShareRow).where(
                DomainFairShareRow.resource_group == resource_group
            )
            domain_result = await db_sess.execute(domain_query)
            domain_fair_shares = {row.domain_name: row.to_data() for row in domain_result.scalars()}

            # Get project fair shares
            project_query = sa.select(ProjectFairShareRow).where(
                ProjectFairShareRow.resource_group == resource_group
            )
            project_result = await db_sess.execute(project_query)
            project_fair_shares = {
                row.project_id: row.to_data() for row in project_result.scalars()
            }

            # Get user fair shares
            user_query = sa.select(UserFairShareRow).where(
                UserFairShareRow.resource_group == resource_group
            )
            user_result = await db_sess.execute(user_query)
            user_fair_shares = {
                (row.user_uuid, row.project_id): row.to_data() for row in user_result.scalars()
            }

            return domain_fair_shares, project_fair_shares, user_fair_shares
