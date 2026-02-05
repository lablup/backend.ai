"""DomainV2 GraphQL data fetchers/loaders package."""

from .domain import fetch_admin_domains, fetch_domain, fetch_rg_domains

__all__ = [
    "fetch_domain",
    "fetch_admin_domains",
    "fetch_rg_domains",
]
