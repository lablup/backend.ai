from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "LOGIN_CLIENT_TYPE_ENTITY_TYPE",
    "LoginClientTypeID",
)


# Raw string mirroring the RBAC-managed EntityType.LOGIN_CLIENT_TYPE value.
LOGIN_CLIENT_TYPE_ENTITY_TYPE = EntityType("login_client_type")


class LoginClientTypeID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return LOGIN_CLIENT_TYPE_ENTITY_TYPE
