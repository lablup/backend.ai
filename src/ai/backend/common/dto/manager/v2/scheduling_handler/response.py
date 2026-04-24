"""Response DTOs for scheduling handler DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.scheduling_handler.types import SchedulingHandlerNode

__all__ = ("ListSchedulingHandlersPayload",)


class ListSchedulingHandlersPayload(BaseResponseModel):
    """Payload listing all registered deployment scheduling handlers."""

    items: list[SchedulingHandlerNode] = Field(
        description="All registered deployment scheduling handlers."
    )
