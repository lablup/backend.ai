"""Admin CLI commands for the system session environ domain."""

from __future__ import annotations

from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
    run_async,
)


@click.group(name="system-session-environ")
def system_session_environ() -> None:
    """Admin system session environ commands."""


@system_session_environ.command(name="resolve")
@click.option(
    "--domain-id", required=True, type=click.UUID, help="The domain the session belongs to."
)
@click.option(
    "--project-id", required=True, type=click.UUID, help="The project the session belongs to."
)
def resolve(domain_id: UUID, project_id: UUID) -> None:
    """Read the rows a session in the domain and project receives (superadmin only)."""
    from ai.backend.common.data.entity.domain import DomainID
    from ai.backend.common.data.entity.project import ProjectID
    from ai.backend.common.dto.manager.v2.system_session_environ.request import (
        AdminResolveSystemSessionEnvironInput,
    )

    request = AdminResolveSystemSessionEnvironInput(
        domain_id=DomainID(domain_id), project_id=ProjectID(project_id)
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.admin_resolve(request)
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
