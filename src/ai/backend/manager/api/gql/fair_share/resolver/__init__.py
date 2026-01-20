"""Fair Share query resolvers package."""

from .domain import domain_fair_share, domain_fair_shares
from .project import project_fair_share, project_fair_shares
from .user import user_fair_share, user_fair_shares

__all__ = [
    "domain_fair_share",
    "domain_fair_shares",
    "project_fair_share",
    "project_fair_shares",
    "user_fair_share",
    "user_fair_shares",
]
