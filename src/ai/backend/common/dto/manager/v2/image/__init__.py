"""
Image DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
    AliasImageInput,
    DealiasImageInput,
    ForgetImageInput,
    ImageFilter,
    ImageFilterInputDTO,
    ImageOrder,
    ImageOrderByInputDTO,
    PurgeImageInput,
    RescanImagesInput,
    SearchImagesInput,
)
from ai.backend.common.dto.manager.v2.image.response import (
    AdminSearchImageAliasesPayload,
    AdminSearchImagesPayload,
    AliasImagePayload,
    ForgetImagePayload,
    GetImagePayload,
    ImageAliasNode,
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
    "AdminSearchImageAliasesInput",
    "AdminSearchImagesInput",
    "AliasImageInput",
    "DealiasImageInput",
    "ForgetImageInput",
    "ImageFilter",
    "ImageFilterInputDTO",
    "ImageOrder",
    "ImageOrderByInputDTO",
    "PurgeImageInput",
    "RescanImagesInput",
    "SearchImagesInput",
    # Response models
    "AdminSearchImageAliasesPayload",
    "AdminSearchImagesPayload",
    "AliasImagePayload",
    "ForgetImagePayload",
    "GetImagePayload",
    "ImageAliasNode",
    "ImageNode",
    "PurgeImagePayload",
    "RescanImagesPayload",
    "SearchImagesPayload",
)
