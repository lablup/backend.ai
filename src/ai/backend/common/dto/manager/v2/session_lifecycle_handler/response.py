"""Response DTOs for session lifecycle handler DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "ListSessionLifecycleHandlersPayload",
    "SessionLifecycleHandlerNode",
)


class SessionLifecycleHandlerNode(BaseResponseModel):
    """Metadata describing a single session lifecycle handler."""

    name: str = Field(
        description="Handler key accepted in the session options' handler_options.by_handler."
    )
    description: str = Field(description="One-line description of what the handler does.")


class ListSessionLifecycleHandlersPayload(BaseResponseModel):
    """Payload listing all registered session lifecycle handlers."""

    items: list[SessionLifecycleHandlerNode] = Field(
        description="All registered session lifecycle handlers."
    )
