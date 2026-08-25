from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.data.notification import NotificationRuleType
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
    NotificationRuleData,
)
from ai.backend.manager.data.notification.types import MatchingNotificationRuleData

from .db_source import NotificationDBSource

if TYPE_CHECKING:
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
    """Reads the dispatch path needs.

    Notification writes run through the generic ops repository, so only what the
    dispatch and validation services read is left here.
    """

    _db_source: NotificationDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = NotificationDBSource(db)

    @notification_repository_resilience.apply()
    async def get_matching_rules(
        self,
        rule_type: NotificationRuleType,
        enabled_only: bool = True,
    ) -> list[MatchingNotificationRuleData]:
        """
        Retrieves all notification rules that match the given rule type.
        """
        return await self._db_source.get_matching_rules(rule_type, enabled_only)

    @notification_repository_resilience.apply()
    async def get_channel_by_id(self, channel_id: UUID) -> NotificationChannelData:
        """Retrieves a notification channel by ID."""
        return await self._db_source.get_channel_by_id(channel_id)

    @notification_repository_resilience.apply()
    async def get_rule_by_id(self, rule_id: UUID) -> NotificationRuleData:
        """Retrieves a notification rule by ID."""
        return await self._db_source.get_rule_by_id(rule_id)
