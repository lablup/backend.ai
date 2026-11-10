from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ClientIPMaskingPolicyEntityType",
    "ClientIPMaskingPolicyID",
)


# One policy row per masking target. Named on its own rather than under the record it
# governs: the same policy answers for login history, login sessions and audit logs.
class ClientIPMaskingPolicyEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "client_ip_masking_policy"

    @override
    @classmethod
    def description(cls) -> str:
        return (
            "How a client address is masked before it is stored in the login history or an"
            " audit log. Without a row of its own or a default row, the address is not masked."
        )


class ClientIPMaskingPolicyID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ClientIPMaskingPolicyEntityType()
