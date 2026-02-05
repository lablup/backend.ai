"""Project V2 GraphQL fetcher package."""

from .project import (
    fetch_admin_projects,
    fetch_domain_projects,
    fetch_project,
    fetch_project_domain,
)

__all__ = [
    "fetch_admin_projects",
    "fetch_domain_projects",
    "fetch_project",
    "fetch_project_domain",
]
