"""
Path parameter DTOs for Prometheus Query Definition API endpoints.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("QueryDefinitionIdPathParam",)


class QueryDefinitionIdPathParam(BaseRequestModel):
    """Path parameter for query definition ID."""

    id: UUID = Field(description="The query definition ID")
