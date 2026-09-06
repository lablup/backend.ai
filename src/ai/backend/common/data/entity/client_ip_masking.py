from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "CLIENT_IP_MASKING_POLICY_ENTITY_TYPE",
    "ClientIPMaskingPolicyID",
)


# One policy row per masking target. Named on its own rather than under the record it
# governs: the same policy answers for login history, login sessions and audit logs.
CLIENT_IP_MASKING_POLICY_ENTITY_TYPE = EntityType("client_ip_masking_policy")


class ClientIPMaskingPolicyID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return CLIENT_IP_MASKING_POLICY_ENTITY_TYPE
