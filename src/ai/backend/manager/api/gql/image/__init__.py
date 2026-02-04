"""
ImageV2 GQL types for Strawberry GraphQL.

This module provides ImageV2 types as part of the Strawberry GraphQL migration (BEP-1010).
See BEP-1038 for detailed specifications.
"""

from .fetcher import fetch_image, fetch_images
from .resolver import (
    admin_images_v2,
    container_registry_images_v2,
    image_v2,
)
from .types import (
    ContainerRegistryScopeGQL,
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
    # Filter, OrderBy, and Scope Types
    "ImageFilterGQL",
    "ImageOrderByGQL",
    "ContainerRegistryScopeGQL",
    # Fetcher functions
    "fetch_images",
    "fetch_image",
    # Resolver fields
    "admin_images_v2",
    "image_v2",
    "container_registry_images_v2",
]
