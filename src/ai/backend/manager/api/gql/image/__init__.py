"""
ImageV2 GQL types for Strawberry GraphQL.

This module provides ImageV2 types as part of the Strawberry GraphQL migration (BEP-1010).
See BEP-1038 for detailed specifications.
"""

from .fetcher import fetch_image, fetch_image_alias, fetch_image_aliases, fetch_images
from .mutations import (
    alias_image,
    clear_image_resource_limit,
    dealias_image,
    forget_image,
    purge_image,
)
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
    ImageV2AliasConnectionGQL,
    ImageV2AliasEdgeGQL,
    ImageV2AliasFilterGQL,
    ImageV2AliasGQL,
    ImageV2AliasOrderByGQL,
    ImageV2AliasOrderFieldGQL,
    ImageV2ConnectionGQL,
    ImageV2EdgeGQL,
    ImageV2FilterGQL,
    ImageV2GQL,
    ImageV2IdentityInfoGQL,
    ImageV2LabelEntryGQL,
    ImageV2MetadataInfoGQL,
    ImageV2OrderByGQL,
    ImageV2OrderFieldGQL,
    ImageV2PermissionGQL,
    ImageV2PermissionInfoGQL,
    ImageV2RequirementsInfoGQL,
    ImageV2ResourceLimitGQL,
    ImageV2ScopeGQL,
    ImageV2StatusGQL,
    ImageV2TagEntryGQL,
)

__all__ = [
    # Enums
    "ImageV2StatusGQL",
    "ImageV2PermissionGQL",
    "ImageV2OrderFieldGQL",
    "ImageV2AliasOrderFieldGQL",
    # Sub-Info Types
    "ImageV2TagEntryGQL",
    "ImageV2LabelEntryGQL",
    "ImageV2ResourceLimitGQL",
    # Info Types
    "ImageV2IdentityInfoGQL",
    "ImageV2MetadataInfoGQL",
    "ImageV2RequirementsInfoGQL",
    "ImageV2PermissionInfoGQL",
    # Main Types
    "ImageV2GQL",
    "ImageV2EdgeGQL",
    "ImageV2ConnectionGQL",
    "ImageV2AliasGQL",
    "ImageV2AliasEdgeGQL",
    "ImageV2AliasConnectionGQL",
    # Filter, OrderBy, and Scope Types
    "ImageV2FilterGQL",
    "ImageV2OrderByGQL",
    "ImageV2AliasFilterGQL",
    "ImageV2AliasOrderByGQL",
    "ContainerRegistryScopeGQL",
    "ImageV2ScopeGQL",
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
    # Mutation fields
    "forget_image",
    "purge_image",
    "alias_image",
    "dealias_image",
    "clear_image_resource_limit",
]
