"""
Response DTOs for Streaming domain.
"""

from __future__ import annotations

from ai.backend.common.api_handlers import BaseRootResponseModel

from .types import StreamAppInfo

__all__ = ("GetStreamAppsResponse",)


class GetStreamAppsResponse(BaseRootResponseModel[list[StreamAppInfo]]):
    """Response for listing available streaming apps/services.

    The handler returns a bare JSON array of service port information.
    """
