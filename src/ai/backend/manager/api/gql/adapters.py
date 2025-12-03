"""GraphQL adapters container."""

from __future__ import annotations

from dataclasses import dataclass

from .artifact import ArtifactGQLAdapter, ArtifactRevisionGQLAdapter
from .notification import NotificationChannelGQLAdapter, NotificationRuleGQLAdapter

__all__ = ("GQLAdapters",)


@dataclass
class GQLAdapters:
    """Container for all GraphQL adapters."""

    notification_channel: NotificationChannelGQLAdapter
    notification_rule: NotificationRuleGQLAdapter
    artifact: ArtifactGQLAdapter
    artifact_revision: ArtifactRevisionGQLAdapter
