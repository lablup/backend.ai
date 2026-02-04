"""Fair Share fetcher module."""

from __future__ import annotations

from .domain import (
    fetch_domain_fair_shares,
    fetch_rg_domain_fair_shares,
    get_domain_fair_share_pagination_spec,
)
from .project import (
    fetch_project_fair_shares,
    fetch_rg_project_fair_shares,
    get_project_fair_share_pagination_spec,
)
from .user import (
    fetch_rg_user_fair_shares,
    fetch_user_fair_shares,
    get_user_fair_share_pagination_spec,
)

__all__ = [
    # Domain
    "fetch_domain_fair_shares",
    "fetch_rg_domain_fair_shares",
    "get_domain_fair_share_pagination_spec",
    # Project
    "fetch_project_fair_shares",
    "fetch_rg_project_fair_shares",
    "get_project_fair_share_pagination_spec",
    # User
    "fetch_user_fair_shares",
    "fetch_rg_user_fair_shares",
    "get_user_fair_share_pagination_spec",
]
