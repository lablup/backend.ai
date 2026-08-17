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
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE
