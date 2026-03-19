"""Fair Share fetcher module."""

from __future__ import annotations

from .domain import (
    fetch_domain_fair_shares,
    fetch_rg_domain_fair_shares,
    fetch_single_domain_fair_share,
)
from .project import (
    fetch_project_fair_shares,
    fetch_rg_project_fair_shares,
    fetch_single_project_fair_share,
)
from .user import (
    fetch_rg_user_fair_shares,
    fetch_single_user_fair_share,
    fetch_user_fair_shares,
)

__all__ = [
    # Domain
    "fetch_domain_fair_shares",
    "fetch_rg_domain_fair_shares",
    "fetch_single_domain_fair_share",
    # Project
    "fetch_project_fair_shares",
    "fetch_rg_project_fair_shares",
    "fetch_single_project_fair_share",
    # User
    "fetch_user_fair_shares",
    "fetch_rg_user_fair_shares",
    "fetch_single_user_fair_share",
]
