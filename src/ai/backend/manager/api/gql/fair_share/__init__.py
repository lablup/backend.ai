"""Fair Share GraphQL API package."""

from .resolver import (
    domain_fair_share,
    domain_fair_shares,
    project_fair_share,
    project_fair_shares,
    user_fair_share,
    user_fair_shares,
)

__all__ = [
    # Domain Fair Share
    "domain_fair_share",
    "domain_fair_shares",
    # Project Fair Share
    "project_fair_share",
    "project_fair_shares",
    # User Fair Share
    "user_fair_share",
    "user_fair_shares",
]
