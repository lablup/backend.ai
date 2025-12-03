from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    from .api.context import RootContext


@asynccontextmanager
async def gql_adapters_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """
    Initialize GraphQL adapters.

    These adapters are created once at server startup and reused across all GraphQL requests.
    """
    from .api.gql.adapters import GQLAdapters
    from .api.gql.artifact import (
        ArtifactGQLAdapter,
        ArtifactRevisionGQLAdapter,
    )
    from .api.gql.notification.adapter import (
        NotificationChannelGQLAdapter,
        NotificationRuleGQLAdapter,
    )
    from .api.gql.scaling_group.adapter import ScalingGroupGQLAdapter

    root_ctx.gql_adapters = GQLAdapters(
        notification_channel=NotificationChannelGQLAdapter(),
        notification_rule=NotificationRuleGQLAdapter(),
        scaling_group=ScalingGroupGQLAdapter(),
        artifact=ArtifactGQLAdapter(),
        artifact_revision=ArtifactRevisionGQLAdapter(),
    )

    yield
