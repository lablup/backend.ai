"""Database source for notification repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationChannelListResult,
    NotificationRuleData,
    NotificationRuleListResult,
    NotificationRuleType,
)
from ai.backend.manager.errors.notification import (
    NotificationChannelNotFound,
    NotificationRuleNotFound,
)
from ai.backend.manager.models.notification import (
    NotificationChannelRow,
    NotificationRuleRow,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    execute_batch_querier,
    execute_creator,
)
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = (
    "NotificationDBSource",
    "NotificationChannelListResult",
    "NotificationRuleListResult",
)


class NotificationDBSource:
    """
    Database source for notification operations.
    Handles all database operations for notification channels and rules.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_matching_rules(
        self,
        rule_type: NotificationRuleType,
        enabled_only: bool = True,
    ) -> list[NotificationRuleData]:
        """Retrieves all notification rules that match the given rule type."""
        async with self._db.begin_readonly_session() as db_sess:
            rows = await self._fetch_matching_rules(db_sess, rule_type, enabled_only)
            return [row.to_data() for row in rows]

    async def _fetch_matching_rules(
        self,
        db_sess: SASession,
        rule_type: NotificationRuleType,
        enabled_only: bool,
    ) -> list[NotificationRuleRow]:
        """Private method to fetch matching rules with channel loaded."""
        query = (
            sa.select(NotificationRuleRow)
            .where(NotificationRuleRow.rule_type == str(rule_type))
            .options(selectinload(NotificationRuleRow.channel))
        )

        if enabled_only:
            query = query.where(NotificationRuleRow.enabled == sa.true())

        result = await db_sess.execute(query)
        rows = list(result.scalars().all())

        # Filter by channel enabled status if needed
        if enabled_only:
            rows = [row for row in rows if row.channel.enabled]

        return rows

    async def create_channel(
        self,
        creator: Creator[NotificationChannelRow],
    ) -> NotificationChannelData:
        """Creates a new notification channel."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    async def update_channel(
        self,
        updater: Updater[NotificationChannelRow],
    ) -> NotificationChannelData:
        """Updates an existing notification channel."""
        async with self._db.begin_session() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise NotificationChannelNotFound(
                    f"Notification channel {updater.pk_value} not found"
                )
            return result.row.to_data()

    async def delete_channel(self, channel_id: UUID) -> bool:
        """Deletes a notification channel."""
        async with self._db.begin_session() as db_sess:
            stmt = sa.delete(NotificationChannelRow).where(NotificationChannelRow.id == channel_id)
            result = await db_sess.execute(stmt)
            return result.rowcount > 0

    async def create_rule(
        self,
        creator: Creator[NotificationRuleRow],
    ) -> NotificationRuleData:
        """Creates a new notification rule."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            # Explicitly load the channel relationship for to_data()
            stmt = (
                sa.select(NotificationRuleRow)
                .where(NotificationRuleRow.id == result.row.id)
                .options(selectinload(NotificationRuleRow.channel))
            )
            query_result = await db_sess.execute(stmt)
            row = query_result.scalar_one()
            return row.to_data()

    async def update_rule(
        self,
        updater: Updater[NotificationRuleRow],
    ) -> NotificationRuleData:
        """Updates an existing notification rule."""
        async with self._db.begin_session() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise NotificationRuleNotFound(f"Notification rule {updater.pk_value} not found")

            # Fetch the updated row with channel relationship loaded
            select_stmt = (
                sa.select(NotificationRuleRow)
                .where(NotificationRuleRow.id == updater.pk_value)
                .options(selectinload(NotificationRuleRow.channel))
            )
            fetch_result = await db_sess.execute(select_stmt)
            row = fetch_result.scalar_one()
            return row.to_data()

    async def delete_rule(self, rule_id: UUID) -> bool:
        """Deletes a notification rule."""
        async with self._db.begin_session() as db_sess:
            stmt = sa.delete(NotificationRuleRow).where(NotificationRuleRow.id == rule_id)
            result = await db_sess.execute(stmt)
            return result.rowcount > 0

    async def get_channel_by_id(self, channel_id: UUID) -> NotificationChannelData:
        """Retrieves a notification channel by ID."""
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.get(NotificationChannelRow, channel_id)
            if not row:
                raise NotificationChannelNotFound(f"Notification channel {channel_id} not found")
            return row.to_data()

    async def get_rule_by_id(self, rule_id: UUID) -> NotificationRuleData:
        """Retrieves a notification rule by ID."""
        async with self._db.begin_readonly_session() as db_sess:
            stmt = (
                sa.select(NotificationRuleRow)
                .where(NotificationRuleRow.id == rule_id)
                .options(selectinload(NotificationRuleRow.channel))
            )
            result = await db_sess.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                raise NotificationRuleNotFound(f"Notification rule {rule_id} not found")
            return row.to_data()

    async def search_channels(
        self,
        querier: BatchQuerier,
    ) -> NotificationChannelListResult:
        """Searches notification channels with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(NotificationChannelRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.NotificationChannelRow.to_data() for row in result.rows]

            return NotificationChannelListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_rules(
        self,
        querier: BatchQuerier,
    ) -> NotificationRuleListResult:
        """Searches notification rules with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(NotificationRuleRow).options(
                selectinload(NotificationRuleRow.channel)
            )

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.NotificationRuleRow.to_data() for row in result.rows]

            return NotificationRuleListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
