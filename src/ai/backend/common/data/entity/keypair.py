from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = (
    "KEYPAIR_FIELD_TYPE",
    "KeyPairID",
)


# Raw string mirroring the RBAC-managed EntityType.KEYPAIR value. It names what the row


KEYPAIR_FIELD_TYPE = FieldType("keypair")


class KeyPairID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KEYPAIR_FIELD_TYPE
