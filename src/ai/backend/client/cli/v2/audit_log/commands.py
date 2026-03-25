"""CLI commands for audit log management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def audit_logs() -> None:
    """Audit log commands."""


@audit_logs.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search audit logs."""
    from ai.backend.common.dto.manager.v2.audit_log.request import AdminSearchAuditLogsInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.audit_log.search(
                AdminSearchAuditLogsInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
