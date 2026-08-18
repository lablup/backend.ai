from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "DOMAIN_USAGE_BUCKET_ENTITY_TYPE",
    "PROJECT_USAGE_BUCKET_ENTITY_TYPE",
    "USER_USAGE_BUCKET_ENTITY_TYPE",
)


# Raw strings mirroring the RBAC-managed EntityType values. A bucket is one owner's usage
# over one window, so the owner's kind is part of what the row is.
DOMAIN_USAGE_BUCKET_ENTITY_TYPE = EntityType("domain:usage_bucket")
PROJECT_USAGE_BUCKET_ENTITY_TYPE = EntityType("project:usage_bucket")
USER_USAGE_BUCKET_ENTITY_TYPE = EntityType("user:usage_bucket")
