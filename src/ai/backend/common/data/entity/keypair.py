from typing import override

from ai.backend.common.data.entity.types import EntityType, FieldIdentifier
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE

__all__ = (
    "KEYPAIR_ENTITY_TYPE",
    "KeyPairID",
)


# Raw string mirroring the RBAC-managed EntityType.KEYPAIR value. It names what the row
# is; a keypair belongs to its user, so the graph holds no node of its own for it.
KEYPAIR_ENTITY_TYPE = EntityType("keypair")


class KeyPairID(FieldIdentifier):
    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE
