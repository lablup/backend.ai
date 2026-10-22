"""GraphQL types for the session lifecycle handler registry."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.session_lifecycle_handler.response import (
    SessionLifecycleHandlerNode,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_pydantic_type
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

__all__ = ("SessionLifecycleHandlerNodeGQL",)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Metadata for a single registered session lifecycle handler. "
            "Surfaces the ``name`` accepted in "
            "``DefaultSessionOptionsInfo.handlerOptions.byHandler``."
        ),
    ),
    model=SessionLifecycleHandlerNode,
    all_fields=True,
    name="SessionLifecycleHandlerNode",
)
class SessionLifecycleHandlerNodeGQL(PydanticOutputMixin[SessionLifecycleHandlerNode]):
    """GraphQL wrapper for :class:`SessionLifecycleHandlerNode`."""

    pass
