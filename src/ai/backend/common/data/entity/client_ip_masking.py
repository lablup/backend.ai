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
        return "A rule masking client addresses in recorded logs."


class ClientIPMaskingPolicyID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ClientIPMaskingPolicyEntityType()
