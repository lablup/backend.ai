from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE",
    "PROJECT_RESOURCE_POLICY_ENTITY_TYPE",
    "USER_RESOURCE_POLICY_ENTITY_TYPE",
)


# Raw strings mirroring the RBAC-managed EntityType.*_RESOURCE_POLICY values.
KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE = EntityType("keypair_resource_policy")
USER_RESOURCE_POLICY_ENTITY_TYPE = EntityType("user_resource_policy")
PROJECT_RESOURCE_POLICY_ENTITY_TYPE = EntityType("project_resource_policy")
