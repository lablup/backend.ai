"""
ImageV2 GQL types for Strawberry GraphQL.

This module provides ImageV2 types as part of the Strawberry GraphQL migration (BEP-1010).
See BEP-1038 for detailed specifications.
"""

from .fetcher import fetch_image, fetch_image_alias, fetch_image_aliases, fetch_images
from .resolver import (
    admin_image_aliases,
    admin_images_v2,
    container_registry_images_v2,
    image_alias,
    image_scoped_aliases,
    image_v2,
)
from .types import (
    ContainerRegistryScopeGQL,
    ImageAliasConnectionGQL,
    ImageAliasEdgeGQL,
    ImageAliasFilterGQL,
    ImageAliasGQL,
    ImageAliasOrderByGQL,
    ImageAliasOrderFieldGQL,
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
    ImageScopeGQL,
    ImageStatusGQL,
    ImageTagEntryGQL,
    ImageV2GQL,
)

__all__ = [
    # Enums
    "ImageStatusGQL",
    "ImagePermissionGQL",
    "ImageOrderFieldGQL",
    "ImageAliasOrderFieldGQL",
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
    "ImageAliasGQL",
    "ImageAliasEdgeGQL",
    "ImageAliasConnectionGQL",
    # Filter, OrderBy, and Scope Types
    "ImageFilterGQL",
    "ImageOrderByGQL",
    "ImageAliasFilterGQL",
    "ImageAliasOrderByGQL",
    "ContainerRegistryScopeGQL",
    "ImageScopeGQL",
    # Fetcher functions
    "fetch_images",
    "fetch_image",
    "fetch_image_alias",
    "fetch_image_aliases",
    # Resolver fields
    "admin_images_v2",
    "image_v2",
    "container_registry_images_v2",
    "image_alias",
    "image_scoped_aliases",
    "admin_image_aliases",
]
