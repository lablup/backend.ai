from typing import override

from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)
from ai.backend.common.data.entity.user import UserEntityType

__all__ = (
    "SSHKeypairFieldType",
    "SSHKeypairID",
)


class SSHKeypairFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "ssh_keypair"

    @override
    @classmethod
    def description(cls) -> str:
        return "An SSH keypair owned by a user."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return UserEntityType


class SSHKeypairID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return SSHKeypairFieldType()
