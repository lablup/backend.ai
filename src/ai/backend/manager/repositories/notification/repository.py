from __future__ import annotations

from typing import Optional
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
    NotificationChannelCreator,
    NotificationChannelData,
    NotificationChannelListResult,
    NotificationChannelModifier,
    NotificationRuleCreator,
    NotificationRuleData,
    NotificationRuleListResult,
    NotificationRuleModifier,
    NotificationRuleType,
)
from ai.backend.manager.repositories.base import Querier

from .db_source import NotificationDBSource

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

    def __init__(self, db_source: NotificationDBSource) -> None:
        self._db_source = db_source

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
        creator: NotificationChannelCreator,
    ) -> NotificationChannelData:
        """Creates a new notification channel."""
        return await self._db_source.create_channel(creator)

    @notification_repository_resilience.apply()
    async def update_channel(
        self,
        channel_id: UUID,
        modifier: NotificationChannelModifier,
    ) -> NotificationChannelData:
        """Updates an existing notification channel."""
        return await self._db_source.update_channel(
            channel_id=channel_id,
            modifier=modifier,
        )

    @notification_repository_resilience.apply()
    async def delete_channel(self, channel_id: UUID) -> bool:
        """Deletes a notification channel."""
        return await self._db_source.delete_channel(channel_id)

    @notification_repository_resilience.apply()
    async def create_rule(
        self,
        creator: NotificationRuleCreator,
    ) -> NotificationRuleData:
        """Creates a new notification rule."""
        return await self._db_source.create_rule(creator)

    @notification_repository_resilience.apply()
    async def update_rule(
        self,
        rule_id: UUID,
        modifier: NotificationRuleModifier,
    ) -> NotificationRuleData:
        """Updates an existing notification rule."""
        return await self._db_source.update_rule(
            rule_id=rule_id,
            modifier=modifier,
        )

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
        querier: Optional[Querier] = None,
    ) -> NotificationChannelListResult:
        """Searches notification channels with total count."""
        return await self._db_source.search_channels(querier=querier)

    @notification_repository_resilience.apply()
    async def search_rules(
        self,
        querier: Optional[Querier] = None,
    ) -> NotificationRuleListResult:
        """Searches notification rules with total count."""
        return await self._db_source.search_rules(querier=querier)
