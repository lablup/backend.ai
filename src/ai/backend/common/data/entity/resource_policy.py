from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE",
    "KeyPairResourcePolicyUUID",
    "PROJECT_RESOURCE_POLICY_ENTITY_TYPE",
    "ProjectResourcePolicyUUID",
    "USER_RESOURCE_POLICY_ENTITY_TYPE",
    "UserResourcePolicyUUID",
)


# Raw strings mirroring the RBAC-managed EntityType.*_RESOURCE_POLICY values.
KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE = EntityType("keypair_resource_policy")
USER_RESOURCE_POLICY_ENTITY_TYPE = EntityType("user_resource_policy")
PROJECT_RESOURCE_POLICY_ENTITY_TYPE = EntityType("project_resource_policy")


class KeyPairResourcePolicyUUID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE


class UserResourcePolicyUUID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE


class ProjectResourcePolicyUUID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return PROJECT_RESOURCE_POLICY_ENTITY_TYPE
