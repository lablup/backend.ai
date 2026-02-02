"""
ImageV2 GQL types for Strawberry GraphQL.

This module provides ImageV2 types as part of the Strawberry GraphQL migration (BEP-1010).
See BEP-1038 for detailed specifications.
"""

from .fetcher import fetch_image, fetch_images
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
    "fetch_image",
    # Resolver fields
    "images_v2",
    "image_v2",
]
