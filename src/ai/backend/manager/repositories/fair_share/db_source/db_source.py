"""Database source for Fair Share repository operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    DomainFairShareSearchResult,
    ProjectFairShareData,
    ProjectFairShareSearchResult,
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
