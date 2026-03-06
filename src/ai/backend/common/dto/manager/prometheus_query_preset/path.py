"""
Path parameter DTOs for Prometheus Query Preset API endpoints.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("PresetIdPathParam",)


class PresetIdPathParam(BaseRequestModel):
    """Path parameter for preset ID."""

    id: UUID = Field(description="The preset ID")
