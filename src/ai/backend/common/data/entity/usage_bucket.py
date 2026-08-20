from ai.backend.common.data.entity.types import FieldType

__all__ = (
    "DOMAIN_USAGE_BUCKET_FIELD_TYPE",
    "PROJECT_USAGE_BUCKET_FIELD_TYPE",
    "USER_USAGE_BUCKET_FIELD_TYPE",
)


# Raw strings mirroring the RBAC-managed EntityType values. A bucket is one owner's usage
# over one window, so the owner's kind is part of what the row is.
DOMAIN_USAGE_BUCKET_FIELD_TYPE = FieldType("domain:usage_bucket")
PROJECT_USAGE_BUCKET_FIELD_TYPE = FieldType("project:usage_bucket")
USER_USAGE_BUCKET_FIELD_TYPE = FieldType("user:usage_bucket")
