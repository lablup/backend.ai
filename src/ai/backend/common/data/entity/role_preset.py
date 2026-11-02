from typing import NewType, override
from uuid import UUID

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RolePresetEntityType",
    "RolePresetID",
    "RolePresetScopeID",
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


# A domain, project or global entity id, discriminated by the preset's scope type. A preset
# whose role is created in every scope of its type has none.
RolePresetScopeID = NewType("RolePresetScopeID", UUID)
