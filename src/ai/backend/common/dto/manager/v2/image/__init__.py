"""
Image DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.image.request import (
    AliasImageInput,
    DealiasImageInput,
    ForgetImageInput,
    ImageFilter,
    ImageOrder,
    PurgeImageInput,
    RescanImagesInput,
    SearchImagesInput,
)
from ai.backend.common.dto.manager.v2.image.response import (
    AliasImagePayload,
    ForgetImagePayload,
    GetImagePayload,
    ImageNode,
    PurgeImagePayload,
    RescanImagesPayload,
    SearchImagesPayload,
)
from ai.backend.common.dto.manager.v2.image.types import (
    ImageLabelInfo,
    ImageOrderField,
    ImageResourceLimitInfo,
    ImageStatusType,
    ImageTagInfo,
    ImageTypeEnum,
    OrderDirection,
)

__all__ = (
    # Types
    "ImageLabelInfo",
    "ImageOrderField",
    "ImageResourceLimitInfo",
    "ImageStatusType",
    "ImageTagInfo",
    "ImageTypeEnum",
    "OrderDirection",
    # Input models (request)
    "AliasImageInput",
    "DealiasImageInput",
    "ForgetImageInput",
    "ImageFilter",
    "ImageOrder",
    "PurgeImageInput",
    "RescanImagesInput",
    "SearchImagesInput",
    # Response models
    "AliasImagePayload",
    "ForgetImagePayload",
    "GetImagePayload",
    "ImageNode",
    "PurgeImagePayload",
    "RescanImagesPayload",
    "SearchImagesPayload",
)
