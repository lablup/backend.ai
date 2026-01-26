"""Fair Share query resolvers package."""

from .domain import (
    bulk_upsert_domain_fair_share_weight,
    domain_fair_share,
    domain_fair_shares,
    upsert_domain_fair_share_weight,
)
from .project import (
    bulk_upsert_project_fair_share_weight,
    project_fair_share,
    project_fair_shares,
    upsert_project_fair_share_weight,
)
from .user import (
    bulk_upsert_user_fair_share_weight,
    upsert_user_fair_share_weight,
    user_fair_share,
    user_fair_shares,
)

__all__ = [
    # Queries
    "domain_fair_share",
    "domain_fair_shares",
    "project_fair_share",
    "project_fair_shares",
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
