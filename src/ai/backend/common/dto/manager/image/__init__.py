"""
Common DTOs for image management used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    AliasImageRequest,
    DealiasImageRequest,
    ForgetImageRequest,
    ImageFilter,
    ImageOrder,
    PurgeImageRequest,
    RescanImagesRequest,
    SearchImagesRequest,
    StringFilter,
)
from .response import (
    AliasImageResponse,
    ForgetImageResponse,
    GetImageResponse,
    ImageDTO,
    PaginationInfo,
    PurgeImageResponse,
    RescanImagesResponse,
    SearchImagesResponse,
)
from .types import (
    ImageOrderField,
    OrderDirection,
)

__all__ = (
    # Types
    "OrderDirection",
    "ImageOrderField",
    # Request DTOs
    "SearchImagesRequest",
    "RescanImagesRequest",
    "AliasImageRequest",
    "DealiasImageRequest",
    "ForgetImageRequest",
    "PurgeImageRequest",
    "StringFilter",
    "ImageFilter",
    "ImageOrder",
    # Response DTOs
    "ImageDTO",
    "SearchImagesResponse",
    "GetImageResponse",
    "RescanImagesResponse",
    "AliasImageResponse",
    "ForgetImageResponse",
    "PurgeImageResponse",
    "PaginationInfo",
)
