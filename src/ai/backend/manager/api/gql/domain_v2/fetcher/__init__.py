"""DomainV2 GraphQL data fetchers/loaders package."""

from .domain import fetch_admin_domains, fetch_domain

__all__ = [
    "fetch_domain",
    "fetch_admin_domains",
]
