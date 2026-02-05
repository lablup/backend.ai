"""Project V2 GraphQL resolver package."""

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
]
