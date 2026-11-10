from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "KeyPairResourcePolicyEntityType",
    "KeyPairResourcePolicyUUID",
    "ProjectResourcePolicyEntityType",
    "ProjectResourcePolicyUUID",
    "UserResourcePolicyEntityType",
    "UserResourcePolicyUUID",
)


class KeyPairResourcePolicyEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "keypair_resource_policy"

    @override
    @classmethod
    def description(cls) -> str:
        return "Resource limits applied per keypair."


class UserResourcePolicyEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "user_resource_policy"

    @override
    @classmethod
    def description(cls) -> str:
        return "Resource limits applied per user."


class ProjectResourcePolicyEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "project_resource_policy"

    @override
    @classmethod
    def description(cls) -> str:
        return "Resource limits applied per project."


class KeyPairResourcePolicyUUID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return KeyPairResourcePolicyEntityType()


class UserResourcePolicyUUID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return UserResourcePolicyEntityType()


class ProjectResourcePolicyUUID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ProjectResourcePolicyEntityType()
