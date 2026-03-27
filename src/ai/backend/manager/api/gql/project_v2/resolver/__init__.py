"""Project V2 GraphQL resolver package."""

from .mutation import (
    admin_create_project_v2,
    admin_delete_project_v2,
    admin_purge_project_v2,
    admin_update_project_v2,
)
from .query import (
    admin_projects_v2,
    domain_projects_v2,
    project_domain_v2,
    project_v2,
)

__all__ = [
    # Queries
    "admin_projects_v2",
    "domain_projects_v2",
    "project_domain_v2",
    "project_v2",
    # Mutations
    "admin_create_project_v2",
    "admin_update_project_v2",
    "admin_delete_project_v2",
    "admin_purge_project_v2",
]
