from typing import override

from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)
from ai.backend.common.data.entity.user import UserEntityType

__all__ = (
    "KeyPairFieldType",
    "KeyPairID",
)


class KeyPairFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "keypair"

    @override
    @classmethod
    def description(cls) -> str:
        return "An access key and secret key pair of a user."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return UserEntityType


class KeyPairID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KeyPairFieldType()
