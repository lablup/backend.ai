"""Fair Share GraphQL API package."""

from .resolver import (
    bulk_upsert_domain_fair_share_weight,
    bulk_upsert_project_fair_share_weight,
    bulk_upsert_user_fair_share_weight,
    domain_fair_share,
    domain_fair_shares,
    project_fair_share,
    project_fair_shares,
    upsert_domain_fair_share_weight,
    upsert_project_fair_share_weight,
    upsert_user_fair_share_weight,
    user_fair_share,
    user_fair_shares,
)

__all__ = [
    # Domain Fair Share Queries
    "domain_fair_share",
    "domain_fair_shares",
    # Project Fair Share Queries
    "project_fair_share",
    "project_fair_shares",
    # User Fair Share Queries
    "user_fair_share",
    "user_fair_shares",
    # Mutations
    "upsert_domain_fair_share_weight",
    "upsert_project_fair_share_weight",
    "upsert_user_fair_share_weight",
    "bulk_upsert_domain_fair_share_weight",
    "bulk_upsert_project_fair_share_weight",
    "bulk_upsert_user_fair_share_weight",
]
