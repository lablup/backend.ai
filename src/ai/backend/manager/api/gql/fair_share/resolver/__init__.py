"""Fair Share query resolvers package."""

from .domain import domain_fair_share, domain_fair_shares, upsert_domain_fair_share_weight
from .project import project_fair_share, project_fair_shares, upsert_project_fair_share_weight
from .user import upsert_user_fair_share_weight, user_fair_share, user_fair_shares

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
]
