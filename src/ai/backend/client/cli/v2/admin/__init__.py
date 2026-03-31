"""Admin CLI command group for v2 REST API.

Registers admin-only sub-groups per entity under
``backend.ai v2 admin {entity} {command}``.
"""

from __future__ import annotations

import click

from ai.backend.common.cli import LazyGroup


@click.group()
def admin() -> None:
    """Admin-only management commands (superadmin required)."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.domain:domain")
def domain() -> None:
    """Admin domain commands."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.user:user")
def user() -> None:
    """Admin user commands."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.project:project")
def project() -> None:
    """Admin project commands."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.agent:agent")
def agent() -> None:
    """Admin agent commands."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.deployment:deployment")
def deployment() -> None:
    """Admin deployment commands."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.image:image")
def image() -> None:
    """Admin image commands."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.session:session")
def session() -> None:
    """Admin session commands."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.artifact:artifact")
def artifact() -> None:
    """Admin artifact commands."""


@admin.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.container_registry:container_registry",
)
def container_registry() -> None:
    """Admin container registry commands."""


@admin.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.login_history:login_history",
)
def login_history() -> None:
    """Admin login history commands."""


@admin.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.login_session:login_session",
)
def login_session() -> None:
    """Admin login session commands."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.export:export")
def export() -> None:
    """Admin CSV export commands."""


@admin.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.service_catalog:service_catalog",
)
def service_catalog() -> None:
    """Admin service catalog commands."""


@admin.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.prometheus_query_preset:prometheus_query_preset",
    name="prometheus-query-definition",
)
def prometheus_query_preset() -> None:
    """Admin prometheus query definition commands."""


@admin.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.resource_allocation:resource_allocation",
    name="resource-allocation",
)
def resource_allocation() -> None:
    """Admin resource allocation commands."""


@admin.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.resource_policy:resource_policy",
    name="resource-policy",
)
def resource_policy() -> None:
    """Admin resource policy commands."""


@admin.group(cls=LazyGroup, import_name="ai.backend.client.cli.v2.admin.keypair:keypair")
def keypair() -> None:
    """Admin keypair commands."""


@admin.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.resource_preset:resource_preset",
    name="resource-preset",
)
def resource_preset() -> None:
    """Admin resource preset commands."""


@admin.group(
    cls=LazyGroup,
    import_name="ai.backend.client.cli.v2.admin.runtime_variant:runtime_variant",
    name="runtime-variant",
)
def runtime_variant() -> None:
    """Admin runtime variant commands."""
