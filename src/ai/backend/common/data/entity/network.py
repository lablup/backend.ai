from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "NetworkEntityType",
    "NetworkID",
)


class NetworkEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "network"

    @override
    @classmethod
    def description(cls) -> str:
        return "A network a network plugin created for a project, that its sessions attach to."


class NetworkID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return NetworkEntityType()
