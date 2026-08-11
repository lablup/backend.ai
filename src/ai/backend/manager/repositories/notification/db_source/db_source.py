"""Database source for notification repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.common.data.notification import NotificationRuleType
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationChannelListResult,
    NotificationRuleData,
    NotificationRuleListResult,
)
from ai.backend.manager.data.notification.types import MatchingNotificationRuleData
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
    execute_batch_querier,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = (
    "NotificationChannelListResult",
    "NotificationDBSource",
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
    ) -> list[MatchingNotificationRuleData]:
        """Retrieves all notification rules that match the given rule type."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            pairs = await self._fetch_matching_rules(db_sess, rule_type, enabled_only)
            return [
                MatchingNotificationRuleData(rule=rule.to_data(), channel=channel.to_data())
                for rule, channel in pairs
            ]

    async def _fetch_matching_rules(
        self,
        db_sess: SASession,
        rule_type: NotificationRuleType,
        enabled_only: bool,
    ) -> list[tuple[NotificationRuleRow, NotificationChannelRow]]:
        """Fetch the rules of one type together with the channel each dispatches through.

        The channel is reached by an explicit join rather than an ORM
        relationship: dispatch both filters on the channel's ``enabled`` flag and
        needs its spec, and a join says so in the statement.
        """
        query = sa.select(NotificationRuleRow, NotificationChannelRow).join(
            NotificationChannelRow,
            NotificationChannelRow.id == NotificationRuleRow.channel_id,
        )
        query = query.where(NotificationRuleRow.rule_type == str(rule_type))

        if enabled_only:
            query = query.where(NotificationRuleRow.enabled == sa.true()).where(
                NotificationChannelRow.enabled == sa.true()
            )

        result = await db_sess.execute(query)
        return [(row.NotificationRuleRow, row.NotificationChannelRow) for row in result.all()]

    async def create_channel(
        self,
        creator: RBACEntityCreator[NotificationChannelRow],
    ) -> NotificationChannelData:
        """Creates a new notification channel."""
        async with self._db.begin_session() as db_sess:
            result = await execute_rbac_entity_creator(db_sess, creator)
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
            return cast(CursorResult[Any], result).rowcount > 0

    async def create_rule(
        self,
        creator: RBACEntityCreator[NotificationRuleRow],
    ) -> NotificationRuleData:
        """Creates a new notification rule."""
        async with self._db.begin_session() as db_sess:
            result = await execute_rbac_entity_creator(db_sess, creator)
            return result.row.to_data()

    async def update_rule(
        self,
        updater: Updater[NotificationRuleRow],
    ) -> NotificationRuleData:
        """Updates an existing notification rule."""
        async with self._db.begin_session() as db_sess:
            result = await execute_updater(db_sess, updater)
            if result is None:
                raise NotificationRuleNotFound(f"Notification rule {updater.pk_value} not found")

            return result.row.to_data()

    async def delete_rule(self, rule_id: UUID) -> bool:
        """Deletes a notification rule."""
        async with self._db.begin_session() as db_sess:
            stmt = sa.delete(NotificationRuleRow).where(NotificationRuleRow.id == rule_id)
            result = await db_sess.execute(stmt)
            return cast(CursorResult[Any], result).rowcount > 0

    async def get_channel_by_id(self, channel_id: UUID) -> NotificationChannelData:
        """Retrieves a notification channel by ID."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.get(NotificationChannelRow, channel_id)
            if not row:
                raise NotificationChannelNotFound(f"Notification channel {channel_id} not found")
            return row.to_data()

    async def get_rule_by_id(self, rule_id: UUID) -> NotificationRuleData:
        """Retrieves a notification rule by ID."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(NotificationRuleRow).where(NotificationRuleRow.id == rule_id)
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
            query = sa.select(NotificationRuleRow)

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
