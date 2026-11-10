from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RolePresetEntityType",
    "RolePresetID",
)


class RolePresetEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "role_preset"

    @override
    @classmethod
    def description(cls) -> str:
        return "A template roles are created from."


class RolePresetID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return RolePresetEntityType()
