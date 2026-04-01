"""Resource Usage query resolvers package."""

from .domain_usage import (
    admin_domain_usage_buckets,
    domain_usage_buckets,
    rg_domain_usage_buckets,
)
from .project_usage import (
    admin_project_usage_buckets,
    project_usage_buckets,
    rg_project_usage_buckets,
)
from .user_usage import (
    admin_user_usage_buckets,
    rg_user_usage_buckets,
    user_usage_buckets,
)

__all__ = [
    # Admin APIs
    "admin_domain_usage_buckets",
    "admin_project_usage_buckets",
    "admin_user_usage_buckets",
    # Resource Group Scoped APIs
    "rg_domain_usage_buckets",
    "rg_project_usage_buckets",
    "rg_user_usage_buckets",
    # Legacy APIs (deprecated)
    "domain_usage_buckets",
    "project_usage_buckets",
    "user_usage_buckets",
]
