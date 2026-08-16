from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ROLE_PERMISSION_PRESET_ENTITY_TYPE",
    "ROLE_PRESET_ENTITY_TYPE",
    "RolePresetID",
)


# Raw strings mirroring the RBAC-managed EntityType values a role preset and its
# permission rows are recorded under.
ROLE_PRESET_ENTITY_TYPE = EntityType("role")
ROLE_PERMISSION_PRESET_ENTITY_TYPE = EntityType("role:permission")


class RolePresetID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE
