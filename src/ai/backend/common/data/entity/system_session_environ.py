from typing import NewType, override
from uuid import UUID

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "SystemSessionEnvironEntityType",
    "SystemSessionEnvironID",
    "SystemSessionEnvironScopeID",
)


class SystemSessionEnvironEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "system_session_environ"

    @override
    @classmethod
    def description(cls) -> str:
        return "A variable the manager injects into the sessions of a scope."


class SystemSessionEnvironID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return SystemSessionEnvironEntityType()


# The public entity, a domain or a project id, discriminated by the accompanying
# ``SystemSessionEnvironScopeType``.
SystemSessionEnvironScopeID = NewType("SystemSessionEnvironScopeID", UUID)
