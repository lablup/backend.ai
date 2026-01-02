from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.policies.retry import BackoffStrategy
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationChannelListResult,
    NotificationRuleData,
    NotificationRuleListResult,
    NotificationRuleType,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator
from ai.backend.manager.repositories.base.updater import Updater

from .db_source import NotificationDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("NotificationRepository",)


notification_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.NOTIFICATION_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
            )
        ),
    ]
)


class NotificationRepository:
    """Repository for notification-related data access."""

    _db_source: NotificationDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = NotificationDBSource(db)

    @notification_repository_resilience.apply()
    async def get_matching_rules(
        self,
        rule_type: NotificationRuleType,
        enabled_only: bool = True,
    ) -> list[NotificationRuleData]:
        """
        Retrieves all notification rules that match the given rule type.
        """
        return await self._db_source.get_matching_rules(rule_type, enabled_only)

    @notification_repository_resilience.apply()
    async def create_channel(
        self,
        creator: Creator[NotificationChannelRow],
    ) -> NotificationChannelData:
        """Creates a new notification channel."""
        return await self._db_source.create_channel(creator)

    @notification_repository_resilience.apply()
    async def update_channel(
        self,
        updater: Updater[NotificationChannelRow],
    ) -> NotificationChannelData:
        """Updates an existing notification channel."""
        return await self._db_source.update_channel(updater=updater)

    @notification_repository_resilience.apply()
    async def delete_channel(self, channel_id: UUID) -> bool:
        """Deletes a notification channel."""
        return await self._db_source.delete_channel(channel_id)

    @notification_repository_resilience.apply()
    async def create_rule(
        self,
        creator: Creator[NotificationRuleRow],
    ) -> NotificationRuleData:
        """Creates a new notification rule."""
        return await self._db_source.create_rule(creator)

    @notification_repository_resilience.apply()
    async def update_rule(
        self,
        updater: Updater[NotificationRuleRow],
    ) -> NotificationRuleData:
        """Updates an existing notification rule."""
        return await self._db_source.update_rule(updater=updater)

    @notification_repository_resilience.apply()
    async def delete_rule(self, rule_id: UUID) -> bool:
        """Deletes a notification rule."""
        return await self._db_source.delete_rule(rule_id)

    @notification_repository_resilience.apply()
    async def get_channel_by_id(self, channel_id: UUID) -> NotificationChannelData:
        """Retrieves a notification channel by ID."""
        return await self._db_source.get_channel_by_id(channel_id)

    @notification_repository_resilience.apply()
    async def get_rule_by_id(self, rule_id: UUID) -> NotificationRuleData:
        """Retrieves a notification rule by ID."""
        return await self._db_source.get_rule_by_id(rule_id)

    @notification_repository_resilience.apply()
    async def search_channels(
        self,
        querier: BatchQuerier,
    ) -> NotificationChannelListResult:
        """Searches notification channels with total count."""
        return await self._db_source.search_channels(querier=querier)

    @notification_repository_resilience.apply()
    async def search_rules(
        self,
        querier: BatchQuerier,
    ) -> NotificationRuleListResult:
        """Searches notification rules with total count."""
        return await self._db_source.search_rules(querier=querier)
