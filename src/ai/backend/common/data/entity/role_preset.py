from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ROLE_PRESET_ENTITY_TYPE",
    "RolePresetID",
)


# Raw string mirroring the RBAC-managed EntityType a role preset is recorded under.
ROLE_PRESET_ENTITY_TYPE = EntityType("role_preset")


class RolePresetID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE
