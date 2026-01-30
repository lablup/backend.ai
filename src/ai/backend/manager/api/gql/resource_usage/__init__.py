"""Resource Usage GraphQL module."""

from __future__ import annotations

from .resolver import (
    admin_domain_usage_buckets,
    admin_project_usage_buckets,
    admin_user_usage_buckets,
    domain_usage_buckets,
    project_usage_buckets,
    rg_domain_usage_buckets,
    rg_project_usage_buckets,
    rg_user_usage_buckets,
    user_usage_buckets,
)
from .types import (
    DomainUsageBucketConnection,
    DomainUsageBucketEdge,
    DomainUsageBucketFilter,
    DomainUsageBucketGQL,
    DomainUsageBucketOrderBy,
    ProjectUsageBucketConnection,
    ProjectUsageBucketEdge,
    ProjectUsageBucketFilter,
    ProjectUsageBucketGQL,
    ProjectUsageBucketOrderBy,
    UsageBucketMetadataGQL,
    UsageBucketOrderField,
    UserUsageBucketConnection,
    UserUsageBucketEdge,
    UserUsageBucketFilter,
    UserUsageBucketGQL,
    UserUsageBucketOrderBy,
)

__all__ = (
    # Admin Resolvers
    "admin_domain_usage_buckets",
    "admin_project_usage_buckets",
    "admin_user_usage_buckets",
    # Resource Group Scoped Resolvers
    "rg_domain_usage_buckets",
    "rg_project_usage_buckets",
    "rg_user_usage_buckets",
    # Legacy Resolvers (deprecated)
    "domain_usage_buckets",
    "project_usage_buckets",
    "user_usage_buckets",
    # Common Types
    "UsageBucketMetadataGQL",
    # Domain Types
    "DomainUsageBucketGQL",
    "DomainUsageBucketConnection",
    "DomainUsageBucketEdge",
    "DomainUsageBucketFilter",
    "DomainUsageBucketOrderBy",
    # Project Types
    "ProjectUsageBucketGQL",
    "ProjectUsageBucketConnection",
    "ProjectUsageBucketEdge",
    "ProjectUsageBucketFilter",
    "ProjectUsageBucketOrderBy",
    # User Types
    "UserUsageBucketGQL",
    "UserUsageBucketConnection",
    "UserUsageBucketEdge",
    "UserUsageBucketFilter",
    "UserUsageBucketOrderBy",
    # Enums
    "UsageBucketOrderField",
)
