from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
    PROJECT_RESOURCE_POLICY_ENTITY_TYPE,
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "KeyPairResourcePolicyUUID",
    "ProjectResourcePolicyUUID",
    "UserResourcePolicyUUID",
)


class KeyPairResourcePolicyUUID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE


class UserResourcePolicyUUID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE


class ProjectResourcePolicyUUID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_RESOURCE_POLICY_ENTITY_TYPE
