"""
Request DTOs for the etcd (config) API endpoints.

Replaces Trafaret schemas used in the legacy ``api/etcd.py`` module.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "GetResourceMetadataQuery",
    "GetConfigRequest",
    "SetConfigRequest",
    "DeleteConfigRequest",
)


class GetResourceMetadataQuery(BaseRequestModel):
    """Query parameters for ``GET /config/resource-slots/details``."""

    sgroup: str | None = Field(
        default=None,
        description="Scaling group name to filter resource metadata by.",
    )


class GetConfigRequest(BaseRequestModel):
    """Request body for ``POST /config/get``."""

    key: str = Field(description="etcd key to read.")
    prefix: bool = Field(
        default=False,
        description="If true, read all keys sharing the given prefix.",
    )


class SetConfigRequest(BaseRequestModel):
    """Request body for ``POST /config/set``."""

    key: str = Field(description="etcd key to write.")
    value: Any = Field(description="Value to store (scalar or nested mapping).")


class DeleteConfigRequest(BaseRequestModel):
    """Request body for ``POST /config/delete``."""

    key: str = Field(description="etcd key to delete.")
    prefix: bool = Field(
        default=False,
        description="If true, delete all keys sharing the given prefix.",
    )
