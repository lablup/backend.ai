"""DomainV2 GraphQL resolvers package."""

from .mutation import (
    admin_create_domain_v2,
    admin_delete_domain_v2,
    admin_purge_domain_v2,
    admin_update_domain_v2,
)
from .query import admin_domains_v2, domain_v2, rg_domains_v2

__all__ = [
    # Queries
    "domain_v2",
    "admin_domains_v2",
    "rg_domains_v2",
    # Mutations
    "admin_create_domain_v2",
    "admin_update_domain_v2",
    "admin_delete_domain_v2",
    "admin_purge_domain_v2",
]
