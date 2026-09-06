from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "NETWORK_ENTITY_TYPE",
    "NetworkID",
)


NETWORK_ENTITY_TYPE = EntityType("network")


class NetworkID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return NETWORK_ENTITY_TYPE
