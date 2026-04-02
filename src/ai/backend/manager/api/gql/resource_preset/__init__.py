"""GraphQL resource preset module."""

from .resolver import (
    admin_create_resource_preset_v2,
    admin_delete_resource_preset_v2,
    admin_resource_preset_v2,
    admin_resource_presets_v2,
    admin_update_resource_preset_v2,
)
from .types import (
    CreateResourcePresetInputGQL,
    CreateResourcePresetPayloadGQL,
    DeleteResourcePresetPayloadGQL,
    ResourcePresetConnection,
    ResourcePresetFilterGQL,
    ResourcePresetGQL,
    ResourcePresetOrderByGQL,
    ResourcePresetOrderFieldGQL,
    UpdateResourcePresetInputGQL,
    UpdateResourcePresetPayloadGQL,
)

__all__ = (
    # Types
    "CreateResourcePresetInputGQL",
    "CreateResourcePresetPayloadGQL",
    "DeleteResourcePresetPayloadGQL",
    "ResourcePresetConnection",
    "ResourcePresetFilterGQL",
    "ResourcePresetGQL",
    "ResourcePresetOrderByGQL",
    "ResourcePresetOrderFieldGQL",
    "UpdateResourcePresetInputGQL",
    "UpdateResourcePresetPayloadGQL",
    # Query Resolvers
    "admin_resource_presets_v2",
    "admin_resource_preset_v2",
    # Mutation Resolvers
    "admin_create_resource_preset_v2",
    "admin_update_resource_preset_v2",
    "admin_delete_resource_preset_v2",
)
