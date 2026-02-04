"""Database source for Fair Share repository operations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, cast

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    DomainFairShareSearchResult,
    FairShareCalculationContext,
    FairShareCalculationSnapshot,
    FairShareMetadata,
    FairSharesByLevel,
    FairShareSpec,
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
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkUpserter,
    BulkUpserterResult,
    Creator,
    Upserter,
    execute_batch_querier,
    execute_bulk_upserter,
    execute_creator,
    execute_upserter,
)
from ai.backend.manager.repositories.fair_share.types import (
    DomainFairShareSearchScope,
    ProjectFairShareSearchScope,
    UserFairShareSearchScope,
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
            spec = await self._fetch_fair_share_spec(db_sess, result.row.resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, result.row.resource_group)
            return result.row.to_data(spec.default_weight, available_slots)

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
            spec = await self._fetch_fair_share_spec(db_sess, result.row.resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, result.row.resource_group)
            return result.row.to_data(spec.default_weight, available_slots)

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
            spec = await self._fetch_fair_share_spec(db_sess, resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, resource_group)
            return row.to_data(spec.default_weight, available_slots)

    async def search_domain_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> DomainFairShareSearchResult:
        """Search domain fair shares with pagination."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DomainFairShareRow)
            result = await execute_batch_querier(db_sess, query, querier)

            # Collect unique resource groups and fetch their specs and capacities
            resource_groups = {row.DomainFairShareRow.resource_group for row in result.rows}
            specs = await self._fetch_fair_share_specs_batch(db_sess, list(resource_groups))
            capacities = {
                rg: await self._fetch_cluster_capacity(db_sess, rg) for rg in resource_groups
            }

            # Convert rows to data with appropriate default_weight and available_slots
            items = [
                row.DomainFairShareRow.to_data(
                    specs[row.DomainFairShareRow.resource_group].default_weight,
                    capacities[row.DomainFairShareRow.resource_group],
                )
                for row in result.rows
            ]
            return DomainFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_domain_fair_shares_by_scope(
        self,
        scope: DomainFairShareSearchScope,
        querier: BatchQuerier,
    ) -> DomainFairShareSearchResult:
        """Search domain fair shares within a scope.

        This method returns all domains associated with a resource group,
        creating default fair share data for domains without records.

        Args:
            scope: Required scope with resource_group.
            querier: Pagination, conditions, and orders for the query.

        Returns:
            DomainFairShareSearchResult with complete fair share data for all domains.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Build LEFT JOIN query: domains associated with resource_group LEFT JOIN fair_share
            query = (
                sa.select(
                    ScalingGroupForDomainRow.scaling_group,
                    ScalingGroupForDomainRow.domain,
                    DomainFairShareRow,
                )
                .select_from(ScalingGroupForDomainRow)
                .outerjoin(
                    DomainFairShareRow,
                    sa.and_(
                        ScalingGroupForDomainRow.scaling_group == DomainFairShareRow.resource_group,
                        ScalingGroupForDomainRow.domain == DomainFairShareRow.domain_name,
                    ),
                )
            )

            result = await execute_batch_querier(db_sess, query, querier, scope)

            # Fetch scaling group spec and available_slots
            spec = await self._fetch_fair_share_spec(db_sess, scope.resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, scope.resource_group)

            items = [
                self._build_domain_fair_share_data(
                    resource_group=row.scaling_group,
                    domain_name=row.domain,
                    fair_share_row=row.DomainFairShareRow,
                    scaling_group_spec=spec,
                    available_slots=available_slots,
                )
                for row in result.rows
            ]

            return DomainFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    def _create_default_domain_fair_share_data(
        self,
        resource_group: str,
        domain_name: str,
        scaling_group_spec: FairShareScalingGroupSpec,
    ) -> DomainFairShareData:
        """Create default domain fair share data when no record exists."""

        now = datetime.now(UTC)
        today = now.date()
        lookback_start = today - timedelta(days=scaling_group_spec.lookback_days)

        return DomainFairShareData(
            id=uuid.UUID(int=0),  # Sentinel UUID for non-persisted record
            resource_group=resource_group,
            domain_name=domain_name,
            spec=FairShareSpec(
                weight=None,
                half_life_days=scaling_group_spec.half_life_days,
                lookback_days=scaling_group_spec.lookback_days,
                decay_unit_days=scaling_group_spec.decay_unit_days,
                resource_weights=scaling_group_spec.resource_weights,
            ),
            calculation_snapshot=FairShareCalculationSnapshot(
                fair_share_factor=Decimal("1.0"),
                total_decayed_usage=ResourceSlot(),
                normalized_usage=Decimal("0.0"),
                lookback_start=lookback_start,
                lookback_end=today,
                last_calculated_at=now,
            ),
            metadata=FairShareMetadata(
                created_at=now,
                updated_at=now,
            ),
            default_weight=scaling_group_spec.default_weight,
            uses_default_resources=[],  # All weights from spec (no merging needed for defaults)
        )

    def _build_domain_fair_share_data(
        self,
        resource_group: str,
        domain_name: str,
        fair_share_row: DomainFairShareRow | None,
        scaling_group_spec: FairShareScalingGroupSpec,
        available_slots: ResourceSlot,
    ) -> DomainFairShareData:
        """Build domain fair share data from query result."""
        if fair_share_row is not None:
            return fair_share_row.to_data(
                scaling_group_spec.default_weight,
                available_slots,
            )
        return self._create_default_domain_fair_share_data(
            resource_group=resource_group,
            domain_name=domain_name,
            scaling_group_spec=scaling_group_spec,
        )

    # ==================== Project Fair Share ====================

    async def create_project_fair_share(
        self,
        creator: Creator[ProjectFairShareRow],
    ) -> ProjectFairShareData:
        """Create a new project fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            spec = await self._fetch_fair_share_spec(db_sess, result.row.resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, result.row.resource_group)
            return result.row.to_data(spec.default_weight, available_slots)

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
            spec = await self._fetch_fair_share_spec(db_sess, result.row.resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, result.row.resource_group)
            return result.row.to_data(spec.default_weight, available_slots)

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
            spec = await self._fetch_fair_share_spec(db_sess, resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, resource_group)
            return row.to_data(spec.default_weight, available_slots)

    async def search_project_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> ProjectFairShareSearchResult:
        """Search project fair shares with pagination."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ProjectFairShareRow)
            result = await execute_batch_querier(db_sess, query, querier)

            # Collect unique resource groups and fetch their specs and capacities
            resource_groups = {row.ProjectFairShareRow.resource_group for row in result.rows}
            specs = await self._fetch_fair_share_specs_batch(db_sess, list(resource_groups))
            capacities = {
                rg: await self._fetch_cluster_capacity(db_sess, rg) for rg in resource_groups
            }

            # Convert rows to data with appropriate default_weight and available_slots
            items = [
                row.ProjectFairShareRow.to_data(
                    specs[row.ProjectFairShareRow.resource_group].default_weight,
                    capacities[row.ProjectFairShareRow.resource_group],
                )
                for row in result.rows
            ]
            return ProjectFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_project_fair_shares_by_scope(
        self,
        scope: ProjectFairShareSearchScope,
        querier: BatchQuerier,
    ) -> ProjectFairShareSearchResult:
        """Search project fair shares within a scope.

        This method returns all projects associated with a resource group,
        creating default fair share data for projects without records.

        Args:
            scope: Required scope with resource_group.
            querier: Pagination, conditions, and orders for the query.

        Returns:
            ProjectFairShareSearchResult with complete fair share data for all projects.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Build LEFT JOIN query: projects associated with resource_group LEFT JOIN fair_share
            query = (
                sa.select(
                    ScalingGroupForProjectRow.scaling_group,
                    ScalingGroupForProjectRow.group.label("project_id"),
                    DomainRow.name.label("domain_name"),
                    ProjectFairShareRow,
                )
                .select_from(ScalingGroupForProjectRow)
                .join(GroupRow, ScalingGroupForProjectRow.group == GroupRow.id)
                .join(DomainRow, GroupRow.domain_name == DomainRow.name)
                .outerjoin(
                    ProjectFairShareRow,
                    sa.and_(
                        ScalingGroupForProjectRow.scaling_group
                        == ProjectFairShareRow.resource_group,
                        ScalingGroupForProjectRow.group == ProjectFairShareRow.project_id,
                    ),
                )
            )

            result = await execute_batch_querier(db_sess, query, querier, scope)

            # Fetch scaling group spec and available_slots
            spec = await self._fetch_fair_share_spec(db_sess, scope.resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, scope.resource_group)

            items = [
                self._build_project_fair_share_data(
                    resource_group=row.scaling_group,
                    project_id=row.project_id,
                    domain_name=row.domain_name,
                    fair_share_row=row.ProjectFairShareRow,
                    scaling_group_spec=spec,
                    available_slots=available_slots,
                )
                for row in result.rows
            ]

            return ProjectFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    def _create_default_project_fair_share_data(
        self,
        resource_group: str,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group_spec: FairShareScalingGroupSpec,
    ) -> ProjectFairShareData:
        """Create default project fair share data when no record exists."""

        now = datetime.now(UTC)
        today = now.date()
        lookback_start = today - timedelta(days=scaling_group_spec.lookback_days)

        return ProjectFairShareData(
            id=uuid.UUID(int=0),  # Sentinel UUID for non-persisted record
            resource_group=resource_group,
            project_id=project_id,
            domain_name=domain_name,
            spec=FairShareSpec(
                weight=None,
                half_life_days=scaling_group_spec.half_life_days,
                lookback_days=scaling_group_spec.lookback_days,
                decay_unit_days=scaling_group_spec.decay_unit_days,
                resource_weights=scaling_group_spec.resource_weights,
            ),
            calculation_snapshot=FairShareCalculationSnapshot(
                fair_share_factor=Decimal("1.0"),
                total_decayed_usage=ResourceSlot(),
                normalized_usage=Decimal("0.0"),
                lookback_start=lookback_start,
                lookback_end=today,
                last_calculated_at=now,
            ),
            metadata=FairShareMetadata(
                created_at=now,
                updated_at=now,
            ),
            default_weight=scaling_group_spec.default_weight,
            uses_default_resources=[],  # All weights from spec (no merging needed for defaults)
        )

    def _build_project_fair_share_data(
        self,
        resource_group: str,
        project_id: uuid.UUID,
        domain_name: str,
        fair_share_row: ProjectFairShareRow | None,
        scaling_group_spec: FairShareScalingGroupSpec,
        available_slots: ResourceSlot,
    ) -> ProjectFairShareData:
        """Build project fair share data from query result."""
        if fair_share_row is not None:
            return fair_share_row.to_data(
                scaling_group_spec.default_weight,
                available_slots,
            )
        return self._create_default_project_fair_share_data(
            resource_group=resource_group,
            project_id=project_id,
            domain_name=domain_name,
            scaling_group_spec=scaling_group_spec,
        )

    # ==================== User Fair Share ====================

    async def create_user_fair_share(
        self,
        creator: Creator[UserFairShareRow],
    ) -> UserFairShareData:
        """Create a new user fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            spec = await self._fetch_fair_share_spec(db_sess, result.row.resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, result.row.resource_group)
            return result.row.to_data(spec.default_weight, available_slots)

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
            spec = await self._fetch_fair_share_spec(db_sess, result.row.resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, result.row.resource_group)
            return result.row.to_data(spec.default_weight, available_slots)

    # ==================== Bulk Upsert Operations ====================

    async def bulk_upsert_domain_fair_share(
        self,
        bulk_upserter: BulkUpserter[DomainFairShareRow],
    ) -> BulkUpserterResult:
        """Bulk upsert domain fair share records.

        Args:
            bulk_upserter: BulkUpserter containing specs for rows to insert/update

        Returns:
            BulkUpserterResult containing count of affected rows
        """
        async with self._db.begin_session_read_committed() as db_sess:
            return await execute_bulk_upserter(
                db_sess,
                bulk_upserter,
                index_elements=["resource_group", "domain_name"],
            )

    async def bulk_upsert_project_fair_share(
        self,
        bulk_upserter: BulkUpserter[ProjectFairShareRow],
    ) -> BulkUpserterResult:
        """Bulk upsert project fair share records.

        Args:
            bulk_upserter: BulkUpserter containing specs for rows to insert/update

        Returns:
            BulkUpserterResult containing count of affected rows
        """
        async with self._db.begin_session_read_committed() as db_sess:
            return await execute_bulk_upserter(
                db_sess,
                bulk_upserter,
                index_elements=["resource_group", "project_id"],
            )

    async def bulk_upsert_user_fair_share(
        self,
        bulk_upserter: BulkUpserter[UserFairShareRow],
    ) -> BulkUpserterResult:
        """Bulk upsert user fair share records.

        Args:
            bulk_upserter: BulkUpserter containing specs for rows to insert/update

        Returns:
            BulkUpserterResult containing count of affected rows
        """
        async with self._db.begin_session_read_committed() as db_sess:
            return await execute_bulk_upserter(
                db_sess,
                bulk_upserter,
                index_elements=["resource_group", "user_uuid", "project_id"],
            )

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
            spec = await self._fetch_fair_share_spec(db_sess, resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, resource_group)
            return row.to_data(spec.default_weight, available_slots)

    async def get_user_project_info(
        self,
        project_id: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> str | None:
        """Get domain_name if user exists in project.

        Returns:
            domain_name if user is member of project, None otherwise.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(GroupRow.domain_name)
                .select_from(AssocGroupUserRow)
                .join(GroupRow, GroupRow.id == AssocGroupUserRow.group_id)
                .where(
                    sa.and_(
                        AssocGroupUserRow.group_id == project_id,
                        AssocGroupUserRow.user_id == user_uuid,
                    )
                )
            )
            result = await db_sess.execute(query)
            return result.scalar_one_or_none()

    async def get_project_info(
        self,
        project_id: uuid.UUID,
    ) -> str | None:
        """Get domain_name if project exists.

        Returns:
            domain_name if project exists, None otherwise.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(GroupRow.domain_name).where(GroupRow.id == project_id)
            result = await db_sess.execute(query)
            return result.scalar_one_or_none()

    async def get_domain_exists(
        self,
        domain_name: str,
    ) -> bool:
        """Check if domain exists.

        Returns:
            True if domain exists, False otherwise.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(sa.literal(1)).where(DomainRow.name == domain_name)
            result = await db_sess.execute(query)
            return result.scalar_one_or_none() is not None

    async def get_scaling_group_fair_share_spec(
        self,
        scaling_group: str,
    ) -> FairShareScalingGroupSpec:
        """Get fair share spec for scaling group.

        Returns:
            FairShareScalingGroupSpec with defaults if not configured.

        Raises:
            ScalingGroupNotFound: If scaling group doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            return await self._fetch_fair_share_spec(db_sess, scaling_group)

    async def search_user_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> UserFairShareSearchResult:
        """Search user fair shares with pagination."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(UserFairShareRow)
            result = await execute_batch_querier(db_sess, query, querier)

            # Collect unique resource groups and fetch their specs and capacities
            resource_groups = {row.UserFairShareRow.resource_group for row in result.rows}
            specs = await self._fetch_fair_share_specs_batch(db_sess, list(resource_groups))
            capacities = {
                rg: await self._fetch_cluster_capacity(db_sess, rg) for rg in resource_groups
            }

            # Convert rows to data with appropriate default_weight and available_slots
            items = [
                row.UserFairShareRow.to_data(
                    specs[row.UserFairShareRow.resource_group].default_weight,
                    capacities[row.UserFairShareRow.resource_group],
                )
                for row in result.rows
            ]
            return UserFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_user_fair_shares_by_scope(
        self,
        scope: UserFairShareSearchScope,
        querier: BatchQuerier,
    ) -> UserFairShareSearchResult:
        """Search user fair shares within a scope.

        This method returns all users associated with a resource group (via project membership),
        creating default fair share data for users without records.

        Args:
            scope: Required scope with resource_group.
            querier: Pagination, conditions, and orders for the query.

        Returns:
            UserFairShareSearchResult with complete fair share data for all users.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Build LEFT JOIN query:
            # Users in projects associated with resource_group LEFT JOIN fair_share
            # Path: ScalingGroupForProjectRow -> AssocGroupUserRow -> UserFairShareRow
            query = (
                sa.select(
                    ScalingGroupForProjectRow.scaling_group,
                    AssocGroupUserRow.user_id.label("user_uuid"),
                    AssocGroupUserRow.group_id.label("project_id"),
                    DomainRow.name.label("domain_name"),
                    UserFairShareRow,
                )
                .select_from(ScalingGroupForProjectRow)
                .join(
                    AssocGroupUserRow, ScalingGroupForProjectRow.group == AssocGroupUserRow.group_id
                )
                .join(GroupRow, ScalingGroupForProjectRow.group == GroupRow.id)
                .join(DomainRow, GroupRow.domain_name == DomainRow.name)
                .outerjoin(
                    UserFairShareRow,
                    sa.and_(
                        ScalingGroupForProjectRow.scaling_group == UserFairShareRow.resource_group,
                        AssocGroupUserRow.user_id == UserFairShareRow.user_uuid,
                        AssocGroupUserRow.group_id == UserFairShareRow.project_id,
                    ),
                )
            )

            result = await execute_batch_querier(db_sess, query, querier, scope)

            # Fetch scaling group spec and available_slots
            spec = await self._fetch_fair_share_spec(db_sess, scope.resource_group)
            available_slots = await self._fetch_cluster_capacity(db_sess, scope.resource_group)

            items = [
                self._build_user_fair_share_data(
                    resource_group=row.scaling_group,
                    user_uuid=row.user_uuid,
                    project_id=row.project_id,
                    domain_name=row.domain_name,
                    fair_share_row=row.UserFairShareRow,
                    scaling_group_spec=spec,
                    available_slots=available_slots,
                )
                for row in result.rows
            ]

            return UserFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    def _create_default_user_fair_share_data(
        self,
        resource_group: str,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group_spec: FairShareScalingGroupSpec,
    ) -> UserFairShareData:
        """Create default user fair share data when no record exists."""

        now = datetime.now(UTC)
        today = now.date()
        lookback_start = today - timedelta(days=scaling_group_spec.lookback_days)

        return UserFairShareData(
            id=uuid.UUID(int=0),  # Sentinel UUID for non-persisted record
            resource_group=resource_group,
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name=domain_name,
            spec=FairShareSpec(
                weight=None,
                half_life_days=scaling_group_spec.half_life_days,
                lookback_days=scaling_group_spec.lookback_days,
                decay_unit_days=scaling_group_spec.decay_unit_days,
                resource_weights=scaling_group_spec.resource_weights,
            ),
            calculation_snapshot=FairShareCalculationSnapshot(
                fair_share_factor=Decimal("1.0"),
                total_decayed_usage=ResourceSlot(),
                normalized_usage=Decimal("0.0"),
                lookback_start=lookback_start,
                lookback_end=today,
                last_calculated_at=now,
            ),
            metadata=FairShareMetadata(
                created_at=now,
                updated_at=now,
            ),
            default_weight=scaling_group_spec.default_weight,
            uses_default_resources=[],  # All weights from spec (no merging needed for defaults)
            scheduling_rank=None,  # No rank calculated yet
        )

    def _build_user_fair_share_data(
        self,
        resource_group: str,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        fair_share_row: UserFairShareRow | None,
        scaling_group_spec: FairShareScalingGroupSpec,
        available_slots: ResourceSlot,
    ) -> UserFairShareData:
        """Build user fair share data from query result."""
        if fair_share_row is not None:
            return fair_share_row.to_data(
                scaling_group_spec.default_weight,
                available_slots,
            )
        return self._create_default_user_fair_share_data(
            resource_group=resource_group,
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name=domain_name,
            scaling_group_spec=scaling_group_spec,
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

            # Upsert domain fair shares
            for domain_name, domain_result in calculation_result.domain_results.items():
                insert_stmt = pg_insert(DomainFairShareRow).values(
                    resource_group=resource_group,
                    domain_name=domain_name,
                    fair_share_factor=domain_result.fair_share_factor,
                    total_decayed_usage=domain_result.total_decayed_usage,
                    normalized_usage=domain_result.normalized_usage,
                    lookback_start=lookback_start,
                    lookback_end=lookback_end,
                    last_calculated_at=now,
                )
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["resource_group", "domain_name"],
                    set_={
                        "fair_share_factor": insert_stmt.excluded.fair_share_factor,
                        "total_decayed_usage": insert_stmt.excluded.total_decayed_usage,
                        "normalized_usage": insert_stmt.excluded.normalized_usage,
                        "lookback_start": insert_stmt.excluded.lookback_start,
                        "lookback_end": insert_stmt.excluded.lookback_end,
                        "last_calculated_at": insert_stmt.excluded.last_calculated_at,
                    },
                )
                await db_sess.execute(upsert_stmt)

            # Upsert project fair shares
            for project_id, project_result in calculation_result.project_results.items():
                insert_stmt = pg_insert(ProjectFairShareRow).values(
                    resource_group=resource_group,
                    project_id=project_id,
                    domain_name=project_result.domain_name,
                    fair_share_factor=project_result.fair_share_factor,
                    total_decayed_usage=project_result.total_decayed_usage,
                    normalized_usage=project_result.normalized_usage,
                    lookback_start=lookback_start,
                    lookback_end=lookback_end,
                    last_calculated_at=now,
                )
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["resource_group", "project_id"],
                    set_={
                        "fair_share_factor": insert_stmt.excluded.fair_share_factor,
                        "total_decayed_usage": insert_stmt.excluded.total_decayed_usage,
                        "normalized_usage": insert_stmt.excluded.normalized_usage,
                        "lookback_start": insert_stmt.excluded.lookback_start,
                        "lookback_end": insert_stmt.excluded.lookback_end,
                        "last_calculated_at": insert_stmt.excluded.last_calculated_at,
                    },
                )
                await db_sess.execute(upsert_stmt)

            # Upsert user fair shares with scheduling ranks
            for user_key, user_result in calculation_result.user_results.items():
                scheduling_rank = rank_by_user.get(user_key)
                insert_stmt = pg_insert(UserFairShareRow).values(
                    resource_group=resource_group,
                    user_uuid=user_key.user_uuid,
                    project_id=user_key.project_id,
                    domain_name=user_result.domain_name,
                    fair_share_factor=user_result.fair_share_factor,
                    total_decayed_usage=user_result.total_decayed_usage,
                    normalized_usage=user_result.normalized_usage,
                    lookback_start=lookback_start,
                    lookback_end=lookback_end,
                    last_calculated_at=now,
                    scheduling_rank=scheduling_rank,
                )
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["resource_group", "user_uuid", "project_id"],
                    set_={
                        "fair_share_factor": insert_stmt.excluded.fair_share_factor,
                        "total_decayed_usage": insert_stmt.excluded.total_decayed_usage,
                        "normalized_usage": insert_stmt.excluded.normalized_usage,
                        "lookback_start": insert_stmt.excluded.lookback_start,
                        "lookback_end": insert_stmt.excluded.lookback_end,
                        "last_calculated_at": insert_stmt.excluded.last_calculated_at,
                        "scheduling_rank": insert_stmt.excluded.scheduling_rank,
                    },
                )
                await db_sess.execute(upsert_stmt)

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
            fair_shares = await self._fetch_fair_shares(db_sess, scaling_group, spec.default_weight)

            # 3. Fetch raw usage buckets (no decay applied)
            raw_usage_buckets = await self._fetch_raw_usage_buckets(
                db_sess, scaling_group, lookback_start, lookback_end
            )

            # 4. Fetch cluster capacity (sum of ALIVE schedulable agents' available_slots)
            cluster_capacity = await self._fetch_cluster_capacity(db_sess, scaling_group)

        return FairShareCalculationContext(
            fair_shares=fair_shares,
            raw_usage_buckets=raw_usage_buckets,
            half_life_days=spec.half_life_days,
            lookback_days=spec.lookback_days,
            default_weight=spec.default_weight,
            resource_weights=spec.resource_weights,
            cluster_capacity=cluster_capacity,
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
            return cast(FairShareScalingGroupSpec, row.fair_share_spec)

        return FairShareScalingGroupSpec()

    async def _fetch_fair_share_specs_batch(
        self,
        db_sess: SASession,
        scaling_groups: Sequence[str],
    ) -> dict[str, FairShareScalingGroupSpec]:
        """Fetch fair share specs for multiple scaling groups.

        Returns a mapping from scaling group name to its fair share spec.
        If a scaling group has no spec configured, returns default spec.
        """
        if not scaling_groups:
            return {}

        result = await db_sess.execute(
            sa.select(
                ScalingGroupRow.name,
                ScalingGroupRow.fair_share_spec,
            ).where(ScalingGroupRow.name.in_(scaling_groups))
        )

        specs: dict[str, FairShareScalingGroupSpec] = {}
        for row in result:
            if row.fair_share_spec is not None:
                specs[row.name] = row.fair_share_spec
            else:
                specs[row.name] = FairShareScalingGroupSpec()

        return specs

    async def _fetch_cluster_capacity(
        self,
        db_sess: SASession,
        scaling_group: str,
    ) -> ResourceSlot:
        """Fetch total available slots from ALIVE schedulable agents in scaling group.

        Args:
            db_sess: Database session
            scaling_group: The scaling group name

        Returns:
            Sum of available_slots from all ALIVE schedulable agents
        """
        query = sa.select(AgentRow.available_slots).where(
            sa.and_(
                AgentRow.scaling_group == scaling_group,
                AgentRow.status == AgentStatus.ALIVE,
                AgentRow.schedulable == sa.true(),
            )
        )
        result = await db_sess.execute(query)
        available_slots_list = result.scalars().all()

        # Sum all available_slots in Python (JSONB aggregation not straightforward in SQL)
        total_capacity = ResourceSlot()
        for slots in available_slots_list:
            if slots:
                total_capacity = total_capacity + slots

        return total_capacity

    async def _fetch_fair_shares(
        self,
        db_sess: SASession,
        scaling_group: str,
        default_weight: Decimal,
    ) -> FairSharesByLevel:
        """Fetch all fair share records for a resource group."""
        # Fetch available_slots once for all conversions
        available_slots = await self._fetch_cluster_capacity(db_sess, scaling_group)

        # Get domain fair shares
        domain_query = sa.select(DomainFairShareRow).where(
            DomainFairShareRow.resource_group == scaling_group
        )
        domain_result = await db_sess.execute(domain_query)
        domain_fair_shares = {
            row.domain_name: row.to_data(default_weight, available_slots)
            for row in domain_result.scalars()
        }

        # Get project fair shares
        project_query = sa.select(ProjectFairShareRow).where(
            ProjectFairShareRow.resource_group == scaling_group
        )
        project_result = await db_sess.execute(project_query)
        project_fair_shares = {
            row.project_id: row.to_data(default_weight, available_slots)
            for row in project_result.scalars()
        }

        # Get user fair shares
        user_query = sa.select(UserFairShareRow).where(
            UserFairShareRow.resource_group == scaling_group
        )
        user_result = await db_sess.execute(user_query)
        user_fair_shares = {
            UserProjectKey(row.user_uuid, row.project_id): row.to_data(
                default_weight, available_slots
            )
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
