"""Database source for Fair Share repository operations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, cast

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot, SlotQuantity
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    DomainFairShareSearchResult,
    FairShareCalculationContext,
    FairShareCalculationSnapshot,
    FairShareData,
    FairShareFactorCalculationResult,
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
from ai.backend.manager.data.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound, ScalingGroupNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UsageBucketEntryRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.user import UserRow
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
    DomainFairShareEntitySearchResult,
    DomainFairShareSearchScope,
    ProjectFairShareEntitySearchResult,
    ProjectFairShareSearchScope,
    UserFairShareEntitySearchResult,
    UserFairShareSearchScope,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


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
            sg_row = await self._fetch_scaling_group_row_by_id(
                db_sess, result.row.resource_group_id
            )
            fair_share_spec = sg_row.fair_share_spec or FairShareScalingGroupSpec()
            available_slots = await self._fetch_available_slots(
                db_sess, result.row.resource_group_id
            )
            return result.row.to_data(
                default_weight=fair_share_spec.default_weight,
                available_slots=available_slots,
            )

    async def upsert_domain_fair_share(
        self,
        upserter: Upserter[DomainFairShareRow],
    ) -> DomainFairShareData:
        """Upsert a domain fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["resource_group_id", "domain_name"],
            )
            fair_share_spec, available_slots = await self._try_fetch_scaling_group_context(
                db_sess, result.row.resource_group_id
            )
            return result.row.to_data(
                default_weight=fair_share_spec.default_weight,
                available_slots=available_slots,
            )

    async def get_domain_fair_share(
        self,
        resource_group_id: ResourceGroupID,
        domain_name: str,
    ) -> DomainFairShareData:
        """Get domain fair share data.

        Steps:
        1. Check if domain exists
        2. Query fair share record with (resource_group, domain_name)
        3. If record exists, convert and return
        4. If no record, create default from scaling group spec

        Raises:
            DomainNotFound: If domain does not exist
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Step 1: Check domain existence (no RG membership required)
            domain_query = sa.select(DomainRow.name).where(DomainRow.name == domain_name)
            domain_result = await db_sess.execute(domain_query)
            if domain_result.one_or_none() is None:
                raise DomainNotFound(domain_name)

            # Step 2: Query fair share record
            fs_query = sa.select(DomainFairShareRow).where(
                DomainFairShareRow.resource_group_id == resource_group_id,
                DomainFairShareRow.domain_name == domain_name,
            )
            fs_result = await db_sess.execute(fs_query)
            fs_row = fs_result.scalar_one_or_none()

            # Step 3: Fetch scaling group row and available slots
            sg_row = await self._fetch_scaling_group_row_by_id(db_sess, resource_group_id)
            fair_share_spec = sg_row.fair_share_spec or FairShareScalingGroupSpec()
            available_slots = await self._fetch_available_slots(db_sess, resource_group_id)

            # Step 4: Return existing record (with merged resource weights)
            if fs_row is not None:
                return fs_row.to_data(
                    default_weight=fair_share_spec.default_weight,
                    available_slots=available_slots,
                )

            # Step 5: Create default from scaling group spec
            now = datetime.now(UTC)
            return self._create_default_domain_fair_share(
                sg_row.name,
                sg_row.id,
                domain_name,
                fair_share_spec,
                available_slots,
                now,
            )

    async def search_domain_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> DomainFairShareSearchResult:
        """Search domain fair shares with pagination."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DomainFairShareRow).outerjoin(
                DomainRow, DomainFairShareRow.domain_name == DomainRow.name
            )
            result = await execute_batch_querier(db_sess, query, querier)

            # Collect unique resource groups and fetch their specs and capacities
            resource_group_ids = {row.DomainFairShareRow.resource_group_id for row in result.rows}
            resource_group_ids_list = list(resource_group_ids)
            specs = await self._fetch_fair_share_specs_batch(db_sess, resource_group_ids_list)
            capacities = await self._fetch_cluster_capacities_batch(
                db_sess, resource_group_ids_list
            )

            # Convert rows to data with appropriate default_weight and available_slots
            items = [
                row.DomainFairShareRow.to_data(
                    specs[row.DomainFairShareRow.resource_group_id].default_weight,
                    capacities[row.DomainFairShareRow.resource_group_id],
                )
                for row in result.rows
            ]
            return DomainFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_rg_domain_fair_shares(
        self,
        scope: DomainFairShareSearchScope,
        querier: BatchQuerier,
    ) -> DomainFairShareEntitySearchResult:
        """Search domain fair shares within a resource group.

        This method returns all domains with complete fair share data
        (either from records or defaults). Domains do not need to be
        registered in the resource group to appear in results.

        Args:
            scope: Required scope with resource_group.
            querier: Pagination, conditions, and orders for the query.

        Returns:
            DomainFairShareEntitySearchResult with domain entities and their complete fair share details.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            sg_row = await self._fetch_scaling_group_row_by_id(db_sess, scope.resource_group_id)
            # Build LEFT JOIN query: all domains LEFT JOIN fair_share (filtered by resource_group)
            query = (
                sa.select(
                    DomainRow.name.label("domain_name"),
                    DomainFairShareRow,
                )
                .select_from(DomainRow)
                .outerjoin(
                    DomainFairShareRow,
                    sa.and_(
                        DomainRow.name == DomainFairShareRow.domain_name,
                        DomainFairShareRow.resource_group_id == scope.resource_group_id,
                    ),
                )
            )

            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            # Fetch scaling group spec AND available_slots for default generation
            spec = await self._fetch_fair_share_spec(db_sess, scope.resource_group_id)
            available_slots = await self._fetch_available_slots(db_sess, scope.resource_group_id)
            now = datetime.now(UTC)

            items = [
                self._build_domain_data(
                    resource_group=sg_row.name,
                    resource_group_id=scope.resource_group_id,
                    domain_name=row.domain_name,
                    fair_share_row=row.DomainFairShareRow,
                    spec=spec,
                    available_slots=available_slots,
                    now=now,
                )
                for row in result.rows
            ]

            return DomainFairShareEntitySearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    def _build_domain_data(
        self,
        resource_group: str,
        resource_group_id: ResourceGroupID,
        domain_name: str,
        fair_share_row: DomainFairShareRow | None,
        spec: FairShareScalingGroupSpec,
        available_slots: list[SlotQuantity],
        now: datetime,
    ) -> DomainFairShareData:
        """Build domain fair share data with complete information.

        Always returns complete DomainFairShareData - either from existing record
        or generated default values.
        """
        if fair_share_row is not None:
            # Has record: convert with merged resource weights
            return fair_share_row.to_data(
                default_weight=spec.default_weight,
                available_slots=available_slots,
            )
        # No record: create default
        return self._create_default_domain_fair_share(
            resource_group, resource_group_id, domain_name, spec, available_slots, now
        )

    # ==================== Project Fair Share ====================

    async def create_project_fair_share(
        self,
        creator: Creator[ProjectFairShareRow],
    ) -> ProjectFairShareData:
        """Create a new project fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            sg_row = await self._fetch_scaling_group_row_by_id(
                db_sess, result.row.resource_group_id
            )
            fair_share_spec = sg_row.fair_share_spec or FairShareScalingGroupSpec()
            available_slots = await self._fetch_available_slots(
                db_sess, result.row.resource_group_id
            )
            return result.row.to_data(
                default_weight=fair_share_spec.default_weight,
                available_slots=available_slots,
            )

    async def upsert_project_fair_share(
        self,
        upserter: Upserter[ProjectFairShareRow],
    ) -> ProjectFairShareData:
        """Upsert a project fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["resource_group_id", "project_id"],
            )
            fair_share_spec, available_slots = await self._try_fetch_scaling_group_context(
                db_sess, result.row.resource_group_id
            )
            return result.row.to_data(
                default_weight=fair_share_spec.default_weight,
                available_slots=available_slots,
            )

    async def get_project_fair_share(
        self,
        resource_group_id: ResourceGroupID,
        project_id: uuid.UUID,
    ) -> ProjectFairShareData:
        """Get project fair share data.

        Steps:
        1. Check if project exists and get domain_name
        2. Query fair share record with (resource_group, project_id)
        3. If record exists, convert and return
        4. If no record, create default from scaling group spec

        Raises:
            ProjectNotFound: If project does not exist
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Step 1: Check project existence and get domain_name (no RG membership required)
            project_query = sa.select(GroupRow.domain_name).where(GroupRow.id == project_id)
            project_result = await db_sess.execute(project_query)
            project_row = project_result.one_or_none()
            if project_row is None:
                raise ProjectNotFound(str(project_id))
            domain_name = project_row[0]

            # Step 2: Query fair share record
            fs_query = sa.select(ProjectFairShareRow).where(
                ProjectFairShareRow.resource_group_id == resource_group_id,
                ProjectFairShareRow.project_id == project_id,
            )
            fs_result = await db_sess.execute(fs_query)
            fs_row = fs_result.scalar_one_or_none()

            # Step 3: Fetch scaling group row and available slots
            sg_row = await self._fetch_scaling_group_row_by_id(db_sess, resource_group_id)
            fair_share_spec = sg_row.fair_share_spec or FairShareScalingGroupSpec()
            available_slots = await self._fetch_available_slots(db_sess, resource_group_id)

            # Step 4: Return existing record (with merged resource weights)
            if fs_row is not None:
                return fs_row.to_data(
                    default_weight=fair_share_spec.default_weight,
                    available_slots=available_slots,
                )

            # Step 5: Create default from scaling group spec
            now = datetime.now(UTC)
            return self._create_default_project_fair_share(
                sg_row.name,
                resource_group_id,
                project_id,
                domain_name,
                fair_share_spec,
                available_slots,
                now,
            )

    async def search_project_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> ProjectFairShareSearchResult:
        """Search project fair shares with pagination."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ProjectFairShareRow).outerjoin(
                GroupRow, ProjectFairShareRow.project_id == GroupRow.id
            )
            result = await execute_batch_querier(db_sess, query, querier)

            # Collect unique resource groups and fetch their specs and capacities
            resource_group_ids = {row.ProjectFairShareRow.resource_group_id for row in result.rows}
            resource_group_ids_list = list(resource_group_ids)
            specs = await self._fetch_fair_share_specs_batch(db_sess, resource_group_ids_list)
            capacities = await self._fetch_cluster_capacities_batch(
                db_sess, resource_group_ids_list
            )

            # Convert rows to data with appropriate default_weight and available_slots
            items = [
                row.ProjectFairShareRow.to_data(
                    specs[row.ProjectFairShareRow.resource_group_id].default_weight,
                    capacities[row.ProjectFairShareRow.resource_group_id],
                )
                for row in result.rows
            ]
            return ProjectFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_rg_project_fair_shares(
        self,
        scope: ProjectFairShareSearchScope,
        querier: BatchQuerier,
    ) -> ProjectFairShareEntitySearchResult:
        """Search project fair shares within a resource group.

        This method returns all projects with complete fair share data
        (either from records or defaults). Projects do not need to be
        registered in the resource group to appear in results.

        Args:
            scope: Required scope with resource_group.
            querier: Pagination, conditions, and orders for the query.

        Returns:
            ProjectFairShareEntitySearchResult with project entities and their complete fair share details.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Build LEFT JOIN query: all projects LEFT JOIN fair_share (filtered by resource_group)
            query = (
                sa.select(
                    GroupRow.id.label("project_id"),
                    GroupRow.domain_name.label("domain_name"),
                    ProjectFairShareRow,
                )
                .select_from(GroupRow)
                .join(DomainRow, GroupRow.domain_name == DomainRow.name)
                .outerjoin(
                    ProjectFairShareRow,
                    sa.and_(
                        GroupRow.id == ProjectFairShareRow.project_id,
                        ProjectFairShareRow.resource_group_id == scope.resource_group_id,
                    ),
                )
            )

            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            # Fetch scaling group spec AND available_slots for default generation
            spec = await self._fetch_fair_share_spec(db_sess, scope.resource_group_id)
            available_slots = await self._fetch_available_slots(db_sess, scope.resource_group_id)
            now = datetime.now(UTC)
            sg_row = await self._fetch_scaling_group_row_by_id(db_sess, scope.resource_group_id)

            items = [
                self._build_project_data(
                    resource_group=sg_row.name,
                    resource_group_id=scope.resource_group_id,
                    project_id=row.project_id,
                    domain_name=row.domain_name,
                    fair_share_row=row.ProjectFairShareRow,
                    spec=spec,
                    available_slots=available_slots,
                    now=now,
                )
                for row in result.rows
            ]

            return ProjectFairShareEntitySearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    def _build_project_data(
        self,
        resource_group: str,
        resource_group_id: ResourceGroupID,
        project_id: uuid.UUID,
        domain_name: str,
        fair_share_row: ProjectFairShareRow | None,
        spec: FairShareScalingGroupSpec,
        available_slots: list[SlotQuantity],
        now: datetime,
    ) -> ProjectFairShareData:
        """Build project fair share data with complete information.

        Always returns complete ProjectFairShareData - either from existing record
        or generated default values.
        """
        if fair_share_row is not None:
            # Has record: convert with merged resource weights
            return fair_share_row.to_data(
                default_weight=spec.default_weight,
                available_slots=available_slots,
            )
        # No record: create default
        return self._create_default_project_fair_share(
            resource_group, resource_group_id, project_id, domain_name, spec, available_slots, now
        )

    # ==================== User Fair Share ====================

    async def create_user_fair_share(
        self,
        creator: Creator[UserFairShareRow],
    ) -> UserFairShareData:
        """Create a new user fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_creator(db_sess, creator)
            sg_row = await self._fetch_scaling_group_row_by_id(
                db_sess, result.row.resource_group_id
            )
            fair_share_spec = sg_row.fair_share_spec or FairShareScalingGroupSpec()
            available_slots = await self._fetch_available_slots(
                db_sess, result.row.resource_group_id
            )
            return result.row.to_data(
                default_weight=fair_share_spec.default_weight,
                available_slots=available_slots,
            )

    async def upsert_user_fair_share(
        self,
        upserter: Upserter[UserFairShareRow],
    ) -> UserFairShareData:
        """Upsert a user fair share record."""
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_upserter(
                db_sess,
                upserter,
                index_elements=["resource_group_id", "user_uuid", "project_id"],
            )
            fair_share_spec, available_slots = await self._try_fetch_scaling_group_context(
                db_sess, result.row.resource_group_id
            )
            return result.row.to_data(
                default_weight=fair_share_spec.default_weight,
                available_slots=available_slots,
            )

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
                index_elements=["resource_group_id", "domain_name"],
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
                index_elements=["resource_group_id", "project_id"],
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
                index_elements=["resource_group_id", "user_uuid", "project_id"],
            )

    async def get_user_fair_share(
        self,
        resource_group_id: ResourceGroupID,
        project_id: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> UserFairShareData:
        """Get user fair share data.

        Steps:
        1. Check if user exists in project (AssocGroupUserRow)
        2. Query fair share record with (resource_group, user_uuid, project_id)
        3. If record exists, convert and return
        4. If no record, create default from scaling group spec

        Raises:
            UserNotFound: If user does not exist in the project
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Step 1: Check user-project association and get domain_name
            assoc_query = (
                sa.select(GroupRow.domain_name)
                .select_from(AssocGroupUserRow)
                .join(GroupRow, AssocGroupUserRow.group_id == GroupRow.id)
                .where(
                    AssocGroupUserRow.group_id == project_id,
                    AssocGroupUserRow.user_id == user_uuid,
                )
            )
            assoc_result = await db_sess.execute(assoc_query)
            assoc_row = assoc_result.one_or_none()
            if assoc_row is None:
                raise UserNotFound(f"User {user_uuid} not found in project {project_id}")
            domain_name = assoc_row[0]

            # Step 2: Query fair share record
            fs_query = sa.select(UserFairShareRow).where(
                UserFairShareRow.resource_group_id == resource_group_id,
                UserFairShareRow.user_uuid == user_uuid,
                UserFairShareRow.project_id == project_id,
            )
            fs_result = await db_sess.execute(fs_query)
            fs_row = fs_result.scalar_one_or_none()

            # Step 3: Fetch scaling group row and available slots
            sg_row = await self._fetch_scaling_group_row_by_id(db_sess, resource_group_id)
            fair_share_spec = sg_row.fair_share_spec or FairShareScalingGroupSpec()
            available_slots = await self._fetch_available_slots(db_sess, resource_group_id)

            # Step 4: Return existing record (with merged resource weights)
            if fs_row is not None:
                return fs_row.to_data(
                    default_weight=fair_share_spec.default_weight,
                    available_slots=available_slots,
                )

            # Step 5: Create default from scaling group spec
            now = datetime.now(UTC)
            return self._create_default_user_fair_share(
                sg_row.name,
                resource_group_id,
                user_uuid,
                project_id,
                domain_name,
                fair_share_spec,
                available_slots,
                now,
            )

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
        resource_group_id: ResourceGroupID,
    ) -> FairShareScalingGroupSpec:
        """Get fair share spec for a resource group.

        Returns:
            FairShareScalingGroupSpec with defaults if not configured.

        Raises:
            ScalingGroupNotFound: If scaling group doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            return await self._fetch_fair_share_spec(db_sess, resource_group_id)

    async def search_user_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> UserFairShareSearchResult:
        """Search user fair shares with pagination."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(UserFairShareRow).outerjoin(
                UserRow, UserFairShareRow.user_uuid == UserRow.uuid
            )
            result = await execute_batch_querier(db_sess, query, querier)

            # Collect unique resource groups and fetch their specs and capacities
            resource_group_ids = {row.UserFairShareRow.resource_group_id for row in result.rows}
            resource_group_ids_list = list(resource_group_ids)
            specs = await self._fetch_fair_share_specs_batch(db_sess, resource_group_ids_list)
            capacities = await self._fetch_cluster_capacities_batch(
                db_sess, resource_group_ids_list
            )

            # Convert rows to data with appropriate default_weight and available_slots
            items = [
                row.UserFairShareRow.to_data(
                    specs[row.UserFairShareRow.resource_group_id].default_weight,
                    capacities[row.UserFairShareRow.resource_group_id],
                )
                for row in result.rows
            ]
            return UserFairShareSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_previous_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_rg_user_fair_shares(
        self,
        scope: UserFairShareSearchScope,
        querier: BatchQuerier,
    ) -> UserFairShareEntitySearchResult:
        """Search user fair shares within a resource group.

        This method returns all users (via project membership) with complete
        fair share data (either from records or defaults). Users do not need
        to be in a project registered in the resource group to appear in results.

        Args:
            scope: Required scope with resource_group.
            querier: Pagination, conditions, and orders for the query.

        Returns:
            UserFairShareEntitySearchResult with user entities and their complete fair share details.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # Build LEFT JOIN query:
            # Users via project membership LEFT JOIN fair_share (filtered by resource_group)
            # Path: AssocGroupUserRow -> GroupRow -> DomainRow -> UserRow -> LEFT JOIN UserFairShareRow
            query = (
                sa.select(
                    AssocGroupUserRow.user_id.label("user_uuid"),
                    AssocGroupUserRow.group_id.label("project_id"),
                    DomainRow.name.label("domain_name"),
                    UserFairShareRow,
                )
                .select_from(AssocGroupUserRow)
                .join(GroupRow, AssocGroupUserRow.group_id == GroupRow.id)
                .join(DomainRow, GroupRow.domain_name == DomainRow.name)
                .join(UserRow, AssocGroupUserRow.user_id == UserRow.uuid)
                .outerjoin(
                    UserFairShareRow,
                    sa.and_(
                        AssocGroupUserRow.user_id == UserFairShareRow.user_uuid,
                        AssocGroupUserRow.group_id == UserFairShareRow.project_id,
                        UserFairShareRow.resource_group_id == scope.resource_group_id,
                    ),
                )
            )

            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            # Fetch scaling group spec AND available_slots for default generation
            sg_row = await self._fetch_scaling_group_row_by_id(db_sess, scope.resource_group_id)
            spec = await self._fetch_fair_share_spec(db_sess, scope.resource_group_id)
            available_slots = await self._fetch_available_slots(db_sess, scope.resource_group_id)
            now = datetime.now(UTC)

            items = [
                self._build_user_data(
                    resource_group=sg_row.name,
                    resource_group_id=scope.resource_group_id,
                    user_uuid=row.user_uuid,
                    project_id=row.project_id,
                    domain_name=row.domain_name,
                    fair_share_row=row.UserFairShareRow,
                    spec=spec,
                    available_slots=available_slots,
                    now=now,
                )
                for row in result.rows
            ]

            return UserFairShareEntitySearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    def _build_user_data(
        self,
        resource_group: str,
        resource_group_id: ResourceGroupID,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        fair_share_row: UserFairShareRow | None,
        spec: FairShareScalingGroupSpec,
        available_slots: list[SlotQuantity],
        now: datetime,
    ) -> UserFairShareData:
        """Build user fair share data with complete information.

        Always returns complete UserFairShareData - either from existing record
        or generated default values.
        """
        if fair_share_row is not None:
            # Has record: convert with merged resource weights
            return fair_share_row.to_data(
                default_weight=spec.default_weight,
                available_slots=available_slots,
            )
        # No record: create default
        return self._create_default_user_fair_share(
            resource_group,
            resource_group_id,
            user_uuid,
            project_id,
            domain_name,
            spec,
            available_slots,
            now,
        )

    async def get_user_scheduling_ranks_batch(
        self,
        resource_group_id: ResourceGroupID,
        project_user_ids: Sequence[ProjectUserIds],
    ) -> dict[uuid.UUID, int]:
        """Get scheduling ranks for multiple users across projects.

        Args:
            resource_group_id: The resource group (scaling group) id.
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
                    UserFairShareRow.resource_group_id == resource_group_id,
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
        resource_group_id: ResourceGroupID,
        calculation_result: FairShareFactorCalculationResult,
        lookback_start: date,
        lookback_end: date,
    ) -> None:
        """Bulk update fair share factors and scheduling ranks for all levels.

        Updates domain, project, and user fair share records with calculated
        factors and ranks in a single transaction.

        Args:
            resource_group_id: The resource group ID being updated
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
                    resource_group_id=resource_group_id,
                    domain_name=domain_name,
                    fair_share_factor=domain_result.fair_share_factor,
                    total_decayed_usage=domain_result.total_decayed_usage,
                    normalized_usage=domain_result.normalized_usage,
                    lookback_start=lookback_start,
                    lookback_end=lookback_end,
                    last_calculated_at=now,
                )
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["resource_group_id", "domain_name"],
                    set_={
                        "resource_group_id": insert_stmt.excluded.resource_group_id,
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
                    resource_group_id=resource_group_id,
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
                    index_elements=["resource_group_id", "project_id"],
                    set_={
                        "resource_group_id": insert_stmt.excluded.resource_group_id,
                        "domain_name": insert_stmt.excluded.domain_name,
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
                    resource_group_id=resource_group_id,
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
                    index_elements=["resource_group_id", "user_uuid", "project_id"],
                    set_={
                        "resource_group_id": insert_stmt.excluded.resource_group_id,
                        "domain_name": insert_stmt.excluded.domain_name,
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
        resource_group_id: ResourceGroupID,
        project_user_ids: Sequence[ProjectUserIds],
    ) -> dict[uuid.UUID, UserFairShareFactors]:
        """Get combined fair share factors for multiple users with 3-way JOIN.

        Fetches domain, project, and user fair share factors in a single query
        by joining the three fair share tables.

        Args:
            resource_group_id: The resource group ID.
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
                        ProjectFairShareRow.resource_group_id == UserFairShareRow.resource_group_id,
                        ProjectFairShareRow.project_id == UserFairShareRow.project_id,
                    ),
                )
                .join(
                    DomainFairShareRow,
                    sa.and_(
                        DomainFairShareRow.resource_group_id == UserFairShareRow.resource_group_id,
                        DomainFairShareRow.domain_name == UserFairShareRow.domain_name,
                    ),
                )
                .where(
                    sa.and_(
                        UserFairShareRow.resource_group_id == resource_group_id,
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
        resource_group_id: ResourceGroupID,
        today: date,
    ) -> FairShareCalculationContext:
        """Get all data needed for fair share factor calculation in a single session.

        Fetches scaling group config, fair share records, and raw usage buckets
        in one database session for consistency and efficiency.

        The Calculator is responsible for applying time decay to raw usage buckets.

        Args:
            resource_group_id: The resource group ID
            today: Current date for decay calculation

        Returns:
            FairShareCalculationContext containing all data for factor calculation

        Raises:
            ScalingGroupNotFound: If the scaling group doesn't exist
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            # 1. Fetch scaling group spec
            spec = await self._fetch_fair_share_spec(db_sess, resource_group_id)

            # Calculate lookback range
            lookback_start = today - timedelta(days=spec.lookback_days)
            lookback_end = today

            # 2. Fetch cluster capacity (sum of ALIVE schedulable agents' available_slots)
            cluster_capacity = await self._fetch_cluster_capacity(db_sess, resource_group_id)

            # 3. Fetch fair shares with resource weights merged
            fair_shares = await self._fetch_fair_shares(
                db_sess,
                resource_group_id,
                spec.default_weight,
                cluster_capacity,
            )

            # 4. Fetch raw usage buckets (no decay applied)
            raw_usage_buckets = await self._fetch_raw_usage_buckets(
                db_sess, resource_group_id, lookback_start, lookback_end
            )

            # 5. Collect project_ids from raw usage buckets and fetch domain names
            project_ids: set[uuid.UUID] = set()
            project_ids.update(raw_usage_buckets.project.keys())
            for user_key in raw_usage_buckets.user:
                project_ids.add(user_key.project_id)
            project_domain_names = await self._fetch_project_domain_names(db_sess, project_ids)

        return FairShareCalculationContext(
            fair_shares=fair_shares,
            raw_usage_buckets=raw_usage_buckets,
            half_life_days=spec.half_life_days,
            lookback_days=spec.lookback_days,
            default_weight=spec.default_weight,
            resource_weights=spec.resource_weights,
            cluster_capacity=cluster_capacity,
            today=today,
            project_domain_names=project_domain_names,
        )

    async def _fetch_project_domain_names(
        self,
        db_sess: SASession,
        project_ids: set[uuid.UUID],
    ) -> dict[uuid.UUID, str]:
        """Fetch domain_name for projects from GroupRow.

        Args:
            db_sess: Database session
            project_ids: Set of project IDs to look up

        Returns:
            Mapping from project_id to domain_name
        """
        if not project_ids:
            return {}
        query = sa.select(GroupRow.id, GroupRow.domain_name).where(GroupRow.id.in_(project_ids))
        result = await db_sess.execute(query)
        return {row.id: row.domain_name for row in result}

    async def _fetch_fair_share_spec(
        self,
        db_sess: SASession,
        resource_group_id: ResourceGroupID,
    ) -> FairShareScalingGroupSpec:
        """Fetch a resource group's fair share spec by ID."""
        result = await db_sess.execute(
            sa.select(
                ScalingGroupRow.id,
                ScalingGroupRow.fair_share_spec,
            ).where(ScalingGroupRow.id == resource_group_id)
        )
        row = result.one_or_none()
        if row is None:
            raise ScalingGroupNotFound(str(resource_group_id))

        if row.fair_share_spec is not None:
            return cast(FairShareScalingGroupSpec, row.fair_share_spec)

        return FairShareScalingGroupSpec()

    async def _fetch_scaling_group_row_by_id(
        self,
        db_sess: SASession,
        resource_group_id: ResourceGroupID,
    ) -> ScalingGroupRow:
        """Fetch a scaling group row by ID.

        Raises:
            ScalingGroupNotFound: If scaling group does not exist
        """
        result = await db_sess.execute(
            sa.select(ScalingGroupRow).where(ScalingGroupRow.id == resource_group_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ScalingGroupNotFound(str(resource_group_id))
        return row

    async def _fetch_scaling_group_row_by_name(
        self,
        db_sess: SASession,
        resource_group_name: str,
    ) -> ScalingGroupRow:
        """Fetch a scaling group row by name.

        Raises:
            ScalingGroupNotFound: If scaling group does not exist
        """
        result = await db_sess.execute(
            sa.select(ScalingGroupRow).where(ScalingGroupRow.name == resource_group_name)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ScalingGroupNotFound(resource_group_name)
        return row

    async def _try_fetch_scaling_group_context(
        self,
        db_sess: SASession,
        resource_group_id: ResourceGroupID,
    ) -> tuple[FairShareScalingGroupSpec, list[SlotQuantity]]:
        """Fetch resource group context, falling back to response defaults."""
        try:
            sg_row = await self._fetch_scaling_group_row_by_id(db_sess, resource_group_id)
            fair_share_spec = sg_row.fair_share_spec or FairShareScalingGroupSpec()
            available_slots = await self._fetch_available_slots(db_sess, sg_row.id)
        except ScalingGroupNotFound:
            fair_share_spec = FairShareScalingGroupSpec()
            available_slots = []
        return fair_share_spec, available_slots

    async def _fetch_available_slots(
        self,
        db_sess: SASession,
        resource_group_id: ResourceGroupID,
    ) -> list[SlotQuantity]:
        """Fetch total available slots from all ALIVE schedulable agents.

        Uses normalized agent_resources table to sum capacity per slot,
        ordered by resource_slot_types.rank.

        Args:
            db_sess: Database session
            resource_group_id: Resource group ID

        Returns:
            Sum of capacity from all ALIVE schedulable agents, rank-ordered
        """
        j = sa.join(AgentResourceRow, AgentRow, AgentResourceRow.agent_id == AgentRow.id).join(
            ResourceSlotTypeRow, AgentResourceRow.slot_name == ResourceSlotTypeRow.slot_name
        )
        query = (
            sa.select(
                AgentResourceRow.slot_name,
                sa.func.sum(AgentResourceRow.capacity).label("total_capacity"),
            )
            .select_from(j)
            .where(
                AgentRow.resource_group_id == resource_group_id,
                AgentRow.status == AgentStatus.ALIVE,
                AgentRow.schedulable.is_(True),
            )
            .group_by(AgentResourceRow.slot_name, ResourceSlotTypeRow.rank)
            .order_by(ResourceSlotTypeRow.rank)
        )
        result = await db_sess.execute(query)
        return [SlotQuantity(row.slot_name, row.total_capacity) for row in result]

    def _create_default_fair_share_data(
        self,
        scaling_group_spec: FairShareScalingGroupSpec,
        available_slots: list[SlotQuantity],
        now: datetime,
    ) -> FairShareData:
        """Create default FairShareData from scaling group spec.

        Used when entity exists but has no fair share record.
        Always sets use_default=True and all resources use default weights.

        Args:
            scaling_group_spec: Scaling group configuration
            available_slots: Scaling group's available slots (for resource keys)
            now: Current datetime for snapshot calculation
        """
        return FairShareData(
            spec=FairShareSpec(
                weight=scaling_group_spec.default_weight,  # Use default_weight
                half_life_days=scaling_group_spec.half_life_days,
                lookback_days=scaling_group_spec.lookback_days,
                decay_unit_days=scaling_group_spec.decay_unit_days,
                resource_weights=scaling_group_spec.resource_weights,
            ),
            calculation_snapshot=FairShareCalculationSnapshot.create_default(
                scaling_group_spec.lookback_days, available_slots, now
            ),
            metadata=None,  # No metadata for default-generated records
            use_default=True,  # Explicitly mark as default
            uses_default_resources=frozenset(
                sq.slot_name for sq in available_slots
            ),  # All resources use defaults
        )

    def _create_default_domain_fair_share(
        self,
        resource_group: str,
        resource_group_id: ResourceGroupID,
        domain_name: str,
        scaling_group_spec: FairShareScalingGroupSpec,
        available_slots: list[SlotQuantity],
        now: datetime,
    ) -> DomainFairShareData:
        """Create default DomainFairShareData.

        Args:
            resource_group: Scaling group name
            domain_name: Domain name
            scaling_group_spec: Scaling group configuration for defaults
            available_slots: Scaling group's available slots (for resource keys)
            now: Current datetime for snapshot calculation
        """
        return DomainFairShareData(
            resource_group=resource_group,
            resource_group_id=resource_group_id,
            domain_name=domain_name,
            data=self._create_default_fair_share_data(scaling_group_spec, available_slots, now),
        )

    def _create_default_project_fair_share(
        self,
        resource_group: str,
        resource_group_id: ResourceGroupID,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group_spec: FairShareScalingGroupSpec,
        available_slots: list[SlotQuantity],
        now: datetime,
    ) -> ProjectFairShareData:
        """Create default ProjectFairShareData.

        Args:
            resource_group: Scaling group name
            project_id: Project ID
            domain_name: Domain name
            scaling_group_spec: Scaling group configuration for defaults
            available_slots: Scaling group's available slots (for resource keys)
            now: Current datetime for snapshot calculation
        """
        return ProjectFairShareData(
            resource_group=resource_group,
            resource_group_id=resource_group_id,
            project_id=project_id,
            domain_name=domain_name,
            data=self._create_default_fair_share_data(scaling_group_spec, available_slots, now),
        )

    def _create_default_user_fair_share(
        self,
        resource_group: str,
        resource_group_id: ResourceGroupID,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group_spec: FairShareScalingGroupSpec,
        available_slots: list[SlotQuantity],
        now: datetime,
    ) -> UserFairShareData:
        """Create default UserFairShareData.

        Args:
            resource_group: Scaling group name
            user_uuid: User UUID
            project_id: Project ID
            domain_name: Domain name
            scaling_group_spec: Scaling group configuration for defaults
            available_slots: Scaling group's available slots (for resource keys)
            now: Current datetime for snapshot calculation
        """
        return UserFairShareData(
            resource_group=resource_group,
            resource_group_id=resource_group_id,
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name=domain_name,
            data=self._create_default_fair_share_data(scaling_group_spec, available_slots, now),
            scheduling_rank=None,
        )

    async def _fetch_fair_share_specs_batch(
        self,
        db_sess: SASession,
        resource_group_ids: Sequence[ResourceGroupID],
    ) -> dict[ResourceGroupID, FairShareScalingGroupSpec]:
        """Fetch fair share specs for multiple resource groups.

        Returns a mapping from resource group ID to its fair share spec.
        If a resource group has no spec configured, returns the default spec.
        """
        if not resource_group_ids:
            return {}

        result = await db_sess.execute(
            sa.select(
                ScalingGroupRow.id,
                ScalingGroupRow.fair_share_spec,
            ).where(ScalingGroupRow.id.in_(resource_group_ids))
        )

        specs: dict[ResourceGroupID, FairShareScalingGroupSpec] = {}
        for row in result:
            if row.fair_share_spec is not None:
                specs[row.id] = row.fair_share_spec
            else:
                specs[row.id] = FairShareScalingGroupSpec()

        return specs

    async def _fetch_cluster_capacity(
        self,
        db_sess: SASession,
        resource_group_id: ResourceGroupID,
    ) -> list[SlotQuantity]:
        """Fetch total capacity from ALIVE schedulable agents in a resource group.

        Uses normalized agent_resources table to sum capacity per slot,
        ordered by resource_slot_types.rank.

        Args:
            db_sess: Database session
            resource_group_id: The resource group ID

        Returns:
            Sum of capacity from all ALIVE schedulable agents, rank-ordered
        """
        j = sa.join(AgentResourceRow, AgentRow, AgentResourceRow.agent_id == AgentRow.id).join(
            ResourceSlotTypeRow, AgentResourceRow.slot_name == ResourceSlotTypeRow.slot_name
        )
        query = (
            sa.select(
                AgentResourceRow.slot_name,
                sa.func.sum(AgentResourceRow.capacity).label("total_capacity"),
            )
            .select_from(j)
            .where(
                sa.and_(
                    AgentRow.resource_group_id == resource_group_id,
                    AgentRow.status == AgentStatus.ALIVE,
                    AgentRow.schedulable == sa.true(),
                )
            )
            .group_by(AgentResourceRow.slot_name, ResourceSlotTypeRow.rank)
            .order_by(ResourceSlotTypeRow.rank)
        )
        result = await db_sess.execute(query)
        return [SlotQuantity(row.slot_name, row.total_capacity) for row in result]

    async def _fetch_cluster_capacities_batch(
        self,
        db_sess: SASession,
        resource_group_ids: Sequence[ResourceGroupID],
    ) -> dict[ResourceGroupID, list[SlotQuantity]]:
        """Fetch total capacity for multiple resource groups.

        Uses normalized agent_resources table to sum capacity per slot per resource group,
        ordered by resource_slot_types.rank.

        Args:
            db_sess: Database session
            resource_group_ids: Resource group IDs

        Returns:
            Mapping from resource group ID to its cluster capacity
        """
        if not resource_group_ids:
            return {}

        j = sa.join(AgentResourceRow, AgentRow, AgentResourceRow.agent_id == AgentRow.id).join(
            ResourceSlotTypeRow, AgentResourceRow.slot_name == ResourceSlotTypeRow.slot_name
        )
        query = (
            sa.select(
                AgentRow.resource_group_id,
                AgentResourceRow.slot_name,
                sa.func.sum(AgentResourceRow.capacity).label("total_capacity"),
            )
            .select_from(j)
            .where(
                sa.and_(
                    AgentRow.resource_group_id.in_(resource_group_ids),
                    AgentRow.status == AgentStatus.ALIVE,
                    AgentRow.schedulable == sa.true(),
                )
            )
            .group_by(
                AgentRow.resource_group_id,
                AgentResourceRow.slot_name,
                ResourceSlotTypeRow.rank,
            )
            .order_by(AgentRow.resource_group_id, ResourceSlotTypeRow.rank)
        )
        result = await db_sess.execute(query)

        capacities: dict[ResourceGroupID, list[SlotQuantity]] = {
            resource_group_id: [] for resource_group_id in resource_group_ids
        }
        for row in result:
            capacities[row.resource_group_id].append(
                SlotQuantity(row.slot_name, row.total_capacity)
            )

        return capacities

    async def _fetch_fair_shares(
        self,
        db_sess: SASession,
        resource_group_id: ResourceGroupID,
        default_weight: Decimal,
        available_slots: list[SlotQuantity],
    ) -> FairSharesByLevel:
        """Fetch all fair share records for a resource group with merged resource weights."""
        # Get domain fair shares
        domain_query = sa.select(DomainFairShareRow).where(
            DomainFairShareRow.resource_group_id == resource_group_id
        )
        domain_result = await db_sess.execute(domain_query)
        domain_fair_shares = {
            row.domain_name: row.to_data(default_weight, available_slots)
            for row in domain_result.scalars()
        }

        # Get project fair shares
        project_query = sa.select(ProjectFairShareRow).where(
            ProjectFairShareRow.resource_group_id == resource_group_id
        )
        project_result = await db_sess.execute(project_query)
        project_fair_shares = {
            row.project_id: row.to_data(default_weight, available_slots)
            for row in project_result.scalars()
        }

        # Get user fair shares
        user_query = sa.select(UserFairShareRow).where(
            UserFairShareRow.resource_group_id == resource_group_id
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
        resource_group_id: ResourceGroupID,
        lookback_start: date,
        lookback_end: date,
    ) -> RawUsageBucketsByLevel:
        """Fetch raw usage buckets from normalized entries without applying decay.

        Reads from usage_bucket_entries joined with parent bucket tables.
        Returns per-date ResourceSlot buckets for each entity.
        The Calculator is responsible for applying time decay to these raw values.
        """
        ube = UsageBucketEntryRow.__table__

        # Fetch user usage buckets via normalized entries
        user_query = (
            sa.select(
                UserUsageBucketRow.user_uuid,
                UserUsageBucketRow.project_id,
                UserUsageBucketRow.period_start,
                ube.c.slot_name,
                ube.c.resource_usage.label("resource_usage"),
            )
            .select_from(
                sa.join(
                    UserUsageBucketRow.__table__,
                    ube,
                    UserUsageBucketRow.__table__.c.id == ube.c.bucket_id,
                )
            )
            .where(
                sa.and_(
                    UserUsageBucketRow.resource_group_id == resource_group_id,
                    UserUsageBucketRow.period_start >= lookback_start,
                    UserUsageBucketRow.period_start <= lookback_end,
                    ube.c.bucket_type == "user",
                )
            )
        )
        user_result = await db_sess.execute(user_query)
        user_rows = user_result.all()

        # Fetch project usage buckets via normalized entries
        project_query = (
            sa.select(
                ProjectUsageBucketRow.project_id,
                ProjectUsageBucketRow.period_start,
                ube.c.slot_name,
                ube.c.resource_usage.label("resource_usage"),
            )
            .select_from(
                sa.join(
                    ProjectUsageBucketRow.__table__,
                    ube,
                    ProjectUsageBucketRow.__table__.c.id == ube.c.bucket_id,
                )
            )
            .where(
                sa.and_(
                    ProjectUsageBucketRow.resource_group_id == resource_group_id,
                    ProjectUsageBucketRow.period_start >= lookback_start,
                    ProjectUsageBucketRow.period_start <= lookback_end,
                    ube.c.bucket_type == "project",
                )
            )
        )
        project_result = await db_sess.execute(project_query)
        project_rows = project_result.all()

        # Fetch domain usage buckets via normalized entries
        domain_query = (
            sa.select(
                DomainUsageBucketRow.domain_name,
                DomainUsageBucketRow.period_start,
                ube.c.slot_name,
                ube.c.resource_usage.label("resource_usage"),
            )
            .select_from(
                sa.join(
                    DomainUsageBucketRow.__table__,
                    ube,
                    DomainUsageBucketRow.__table__.c.id == ube.c.bucket_id,
                )
            )
            .where(
                sa.and_(
                    DomainUsageBucketRow.resource_group_id == resource_group_id,
                    DomainUsageBucketRow.period_start >= lookback_start,
                    DomainUsageBucketRow.period_start <= lookback_end,
                    ube.c.bucket_type == "domain",
                )
            )
        )
        domain_result = await db_sess.execute(domain_query)
        domain_rows = domain_result.all()

        # Organize into per-date ResourceSlot buckets (no decay applied)
        user_buckets: dict[UserProjectKey, dict[date, ResourceSlot]] = {}
        for row in user_rows:
            key = UserProjectKey(row.user_uuid, row.project_id)
            if key not in user_buckets:
                user_buckets[key] = {}
            if row.period_start not in user_buckets[key]:
                user_buckets[key][row.period_start] = ResourceSlot()
            user_buckets[key][row.period_start][row.slot_name] = Decimal(str(row.resource_usage))

        project_buckets: dict[uuid.UUID, dict[date, ResourceSlot]] = {}
        for row in project_rows:
            if row.project_id not in project_buckets:
                project_buckets[row.project_id] = {}
            if row.period_start not in project_buckets[row.project_id]:
                project_buckets[row.project_id][row.period_start] = ResourceSlot()
            project_buckets[row.project_id][row.period_start][row.slot_name] = Decimal(
                str(row.resource_usage)
            )

        domain_buckets: dict[str, dict[date, ResourceSlot]] = {}
        for row in domain_rows:
            if row.domain_name not in domain_buckets:
                domain_buckets[row.domain_name] = {}
            if row.period_start not in domain_buckets[row.domain_name]:
                domain_buckets[row.domain_name][row.period_start] = ResourceSlot()
            domain_buckets[row.domain_name][row.period_start][row.slot_name] = Decimal(
                str(row.resource_usage)
            )

        return RawUsageBucketsByLevel(
            domain=domain_buckets,
            project=project_buckets,
            user=user_buckets,
        )
