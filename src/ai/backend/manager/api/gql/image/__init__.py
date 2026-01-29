"""
ImageV2 GQL types for Strawberry GraphQL.

This module provides ImageV2 types as part of the Strawberry GraphQL migration (BEP-1010).
See BEP-1038 for detailed specifications.
"""

from .fetcher import fetch_image_by_id, fetch_images
from .mutations import (
    alias_image,
    clear_image_resource_limit,
    dealias_image,
    forget_image,
    purge_image,
)
from .resolver import image_v2, images_v2
from .types import (
    ImageConnectionV2GQL,
    ImageEdgeGQL,
    ImageFilterGQL,
    ImageIdentityInfoGQL,
    ImageLabelEntryGQL,
    ImageMetadataInfoGQL,
    ImageOrderByGQL,
    ImageOrderFieldGQL,
    ImagePermissionGQL,
    ImagePermissionInfoGQL,
    ImageRequirementsInfoGQL,
    ImageResourceLimitGQL,
    ImageStatusGQL,
    ImageTagEntryGQL,
    ImageV2GQL,
)

__all__ = [
    # Enums
    "ImageStatusGQL",
    "ImagePermissionGQL",
    "ImageOrderFieldGQL",
    # Sub-Info Types
    "ImageTagEntryGQL",
    "ImageLabelEntryGQL",
    "ImageResourceLimitGQL",
    # Info Types
    "ImageIdentityInfoGQL",
    "ImageMetadataInfoGQL",
    "ImageRequirementsInfoGQL",
    "ImagePermissionInfoGQL",
    # Main Types
    "ImageV2GQL",
    "ImageEdgeGQL",
    "ImageConnectionV2GQL",
    # Filter and OrderBy Types
    "ImageFilterGQL",
    "ImageOrderByGQL",
    # Fetcher functions
    "fetch_images",
    "fetch_image_by_id",
    # Resolver fields (Queries)
    "images_v2",
    "image_v2",
    # Mutation fields
    "forget_image",
    "purge_image",
    "alias_image",
    "dealias_image",
    "clear_image_resource_limit",
]
