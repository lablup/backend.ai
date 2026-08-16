from typing import override

from ai.backend.common.data.entity.login_client_type import LOGIN_CLIENT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("LoginClientTypeID",)


class LoginClientTypeID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return LOGIN_CLIENT_TYPE_ENTITY_TYPE
