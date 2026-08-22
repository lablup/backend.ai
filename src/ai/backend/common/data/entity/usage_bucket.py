from ai.backend.common.data.entity.types import FieldType

__all__ = (
    "DOMAIN_USAGE_BUCKET_FIELD_TYPE",
    "PROJECT_USAGE_BUCKET_FIELD_TYPE",
    "USER_USAGE_BUCKET_FIELD_TYPE",
)


# A bucket is one owner's usage over one window, so the owner's kind is part of what the
# row is. The legacy RBAC `EntityType` spells the same pair with a `:`; a field type is
# one name.
DOMAIN_USAGE_BUCKET_FIELD_TYPE = FieldType("domain_usage_bucket")
PROJECT_USAGE_BUCKET_FIELD_TYPE = FieldType("project_usage_bucket")
USER_USAGE_BUCKET_FIELD_TYPE = FieldType("user_usage_bucket")
