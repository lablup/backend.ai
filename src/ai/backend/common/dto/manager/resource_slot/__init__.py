"""
Common DTOs for resource slot type management.
"""

from __future__ import annotations

from .request import (
    OrderDirection,
    ResourceSlotTypeFilter,
    ResourceSlotTypeOrder,
    ResourceSlotTypeOrderField,
    ResourceSlotTypePathParam,
    SearchResourceSlotTypesRequest,
)
from .response import (
    GetResourceSlotTypeResponse,
    NumberFormatDTO,
    PaginationInfo,
    ResourceSlotTypeDTO,
    SearchResourceSlotTypesResponse,
)

__all__ = (
    # Request DTOs
    "OrderDirection",
    "ResourceSlotTypeFilter",
    "ResourceSlotTypeOrder",
    "ResourceSlotTypeOrderField",
    "ResourceSlotTypePathParam",
    "SearchResourceSlotTypesRequest",
    # Response DTOs
    "NumberFormatDTO",
    "ResourceSlotTypeDTO",
    "PaginationInfo",
    "SearchResourceSlotTypesResponse",
    "GetResourceSlotTypeResponse",
)
