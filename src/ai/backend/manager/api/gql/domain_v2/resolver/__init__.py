"""DomainV2 GraphQL resolvers package."""

from .query import admin_domains_v2, domain_v2

__all__ = [
    "domain_v2",
    "admin_domains_v2",
]
