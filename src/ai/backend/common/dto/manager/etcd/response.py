"""
Response DTOs for the etcd (config) API endpoints.

These models describe the JSON shapes returned by the new-style
``EtcdHandler`` methods.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel, BaseRootResponseModel

__all__ = (
    "ResourceSlotsResponse",
    "ResourceMetadataResponse",
    "VfolderTypesResponse",
    "ConfigResultResponse",
    "OkResultResponse",
)


class ResourceSlotsResponse(BaseRootResponseModel[dict[str, str]]):
    """Bare dict mapping slot name → slot type string."""


class ResourceMetadataResponse(BaseRootResponseModel[dict[str, Any]]):
    """Bare dict mapping slot name → accelerator metadata object."""


class VfolderTypesResponse(BaseRootResponseModel[list[str]]):
    """Bare list of available vfolder type strings."""


class ConfigResultResponse(BaseResponseModel):
    """Response for ``POST /config/get``."""

    result: Any = Field(description="The value read from etcd.")


class OkResultResponse(BaseResponseModel):
    """Response for ``POST /config/set`` and ``POST /config/delete``."""

    result: str = Field(default="ok")
