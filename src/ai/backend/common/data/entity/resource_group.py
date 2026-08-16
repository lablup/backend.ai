import uuid
from typing import NewType, override

from ai.backend.common.data.entity.types import EntityType, NaturalKey, ScopeType

__all__ = (
    "RESOURCE_GROUP_ENTITY_TYPE",
    "RESOURCE_GROUP_SCOPE_TYPE",
    "ResourceGroupID",
    "ResourceGroupName",
)


# Raw strings mirroring the RBAC-managed RBACElementType.RESOURCE_GROUP value.
RESOURCE_GROUP_ENTITY_TYPE = EntityType("resource_group")
RESOURCE_GROUP_SCOPE_TYPE = ScopeType(RESOURCE_GROUP_ENTITY_TYPE)

ResourceGroupID = NewType("ResourceGroupID", uuid.UUID)


class ResourceGroupName(NaturalKey):
    @override
    @classmethod
    def key_name(cls) -> str:
        return "resource_group_name"
