"""
Response DTOs for system DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("SystemVersionNode",)


class SystemVersionNode(BaseResponseModel):
    """Node representing the system version information."""

    version: str = Field(description="API version string.")
    manager: str = Field(description="Manager version string.")
