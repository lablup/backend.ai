"""Fair Share query resolvers package."""

from .domain import (
    admin_bulk_upsert_domain_fair_share_weight,
    admin_domain_fair_share,
    admin_domain_fair_shares,
    admin_upsert_domain_fair_share_weight,
    bulk_upsert_domain_fair_share_weight,
    domain_fair_share,
    domain_fair_shares,
    rg_domain_fair_share,
    rg_domain_fair_shares,
    upsert_domain_fair_share_weight,
)
from .project import (
    admin_bulk_upsert_project_fair_share_weight,
    admin_project_fair_share,
    admin_project_fair_shares,
    admin_upsert_project_fair_share_weight,
    bulk_upsert_project_fair_share_weight,
    project_fair_share,
    project_fair_shares,
    rg_project_fair_share,
    rg_project_fair_shares,
    upsert_project_fair_share_weight,
)
from .user import (
    admin_bulk_upsert_user_fair_share_weight,
    admin_upsert_user_fair_share_weight,
    admin_user_fair_share,
    admin_user_fair_shares,
    bulk_upsert_user_fair_share_weight,
    rg_user_fair_share,
    rg_user_fair_shares,
    upsert_user_fair_share_weight,
    user_fair_share,
    user_fair_shares,
)

__all__ = [
    # Admin Queries
    "admin_domain_fair_share",
    "admin_domain_fair_shares",
    "admin_project_fair_share",
    "admin_project_fair_shares",
    "admin_user_fair_share",
    "admin_user_fair_shares",
    # Admin Mutations
    "admin_upsert_domain_fair_share_weight",
    "admin_upsert_project_fair_share_weight",
    "admin_upsert_user_fair_share_weight",
    "admin_bulk_upsert_domain_fair_share_weight",
    "admin_bulk_upsert_project_fair_share_weight",
    "admin_bulk_upsert_user_fair_share_weight",
    # Resource Group Scoped Queries
    "rg_domain_fair_share",
    "rg_domain_fair_shares",
    "rg_project_fair_share",
    "rg_project_fair_shares",
    "rg_user_fair_share",
    "rg_user_fair_shares",
    # Legacy Queries (deprecated)
    "domain_fair_share",
    "domain_fair_shares",
    "project_fair_share",
    "project_fair_shares",
    "user_fair_share",
    "user_fair_shares",
    # Legacy Mutations (deprecated)
    "upsert_domain_fair_share_weight",
    "upsert_project_fair_share_weight",
    "upsert_user_fair_share_weight",
    "bulk_upsert_domain_fair_share_weight",
    "bulk_upsert_project_fair_share_weight",
    "bulk_upsert_user_fair_share_weight",
]
