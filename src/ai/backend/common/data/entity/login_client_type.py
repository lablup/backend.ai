from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "LoginClientTypeEntityType",
    "LoginClientTypeID",
)


class LoginClientTypeEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "login_client_type"

    @override
    @classmethod
    def description(cls) -> str:
        return "A kind of client a login session is opened from."


class LoginClientTypeID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return LoginClientTypeEntityType()
