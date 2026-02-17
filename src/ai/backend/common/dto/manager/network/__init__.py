"""
Common DTOs for network system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    CreateNetworkRequest,
    DeleteNetworkRequest,
    NetworkFilter,
    NetworkOrder,
    SearchNetworksRequest,
    UpdateNetworkRequest,
)
from .response import (
    CreateNetworkResponse,
    DeleteNetworkResponse,
    GetNetworkResponse,
    NetworkDTO,
    PaginationInfo,
    SearchNetworksResponse,
    UpdateNetworkResponse,
)
from .types import (
    NetworkOrderField,
    OrderDirection,
)

__all__ = (
    # Types
    "OrderDirection",
    "NetworkOrderField",
    # Request DTOs
    "CreateNetworkRequest",
    "UpdateNetworkRequest",
    "SearchNetworksRequest",
    "DeleteNetworkRequest",
    "NetworkFilter",
    "NetworkOrder",
    # Response DTOs
    "NetworkDTO",
    "PaginationInfo",
    "CreateNetworkResponse",
    "GetNetworkResponse",
    "SearchNetworksResponse",
    "UpdateNetworkResponse",
    "DeleteNetworkResponse",
)
