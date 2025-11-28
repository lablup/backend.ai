"""GraphQL adapters container."""

from __future__ import annotations

from dataclasses import dataclass

from .notification import NotificationChannelGQLAdapter, NotificationRuleGQLAdapter
from .scaling_group import ScalingGroupGQLAdapter

__all__ = ("GQLAdapters",)


@dataclass
class GQLAdapters:
    """Container for all GraphQL adapters."""

    notification_channel: NotificationChannelGQLAdapter
    notification_rule: NotificationRuleGQLAdapter
    scaling_group: ScalingGroupGQLAdapter
