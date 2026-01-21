from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.notification.options import (
    NotificationChannelConditions,
    NotificationRuleConditions,
)
from ai.backend.manager.services.notification.actions.list_channels import SearchChannelsAction
from ai.backend.manager.services.notification.actions.list_rules import SearchRulesAction
from ai.backend.manager.services.notification.processors import NotificationProcessors


async def load_channels_by_ids(
    processor: NotificationProcessors,
    channel_ids: Sequence[uuid.UUID],
) -> list[Optional[NotificationChannelData]]:
    """Batch load notification channels by their IDs.

    Args:
        processor: The notification processor.
        channel_ids: Sequence of channel UUIDs to load.

    Returns:
        List of NotificationChannelData (or None if not found) in the same order as channel_ids.
    """
    if not channel_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(channel_ids)),
        conditions=[NotificationChannelConditions.by_ids(channel_ids)],
    )

    action_result = await processor.search_channels.wait_for_complete(
        SearchChannelsAction(querier=querier)
    )

    channel_map = {channel.id: channel for channel in action_result.channels}
    return [channel_map.get(channel_id) for channel_id in channel_ids]


async def load_rules_by_ids(
    processor: NotificationProcessors,
    rule_ids: Sequence[uuid.UUID],
) -> list[Optional[NotificationRuleData]]:
    """Batch load notification rules by their IDs.

    Args:
        processor: The notification processor.
        rule_ids: Sequence of rule UUIDs to load.

    Returns:
        List of NotificationRuleData (or None if not found) in the same order as rule_ids.
    """
    if not rule_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(rule_ids)),
        conditions=[NotificationRuleConditions.by_ids(rule_ids)],
    )

    action_result = await processor.search_rules.wait_for_complete(
        SearchRulesAction(querier=querier)
    )

    rule_map = {rule.id: rule for rule in action_result.rules}
    return [rule_map.get(rule_id) for rule_id in rule_ids]
