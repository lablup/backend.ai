from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import click

from ai.backend.manager.network.ipam import (
    overlay_encryption_key_status,
    rotate_overlay_encryption_key,
)

if TYPE_CHECKING:
    from ai.backend.manager.cli.context import CLIContext


@click.group()
def cli() -> None:
    """Inspect and maintain the cluster network."""


def _display_timestamp(value: float | None) -> str:
    if value is None:
        return "unknown"
    return datetime.fromtimestamp(value, tz=UTC).isoformat()


@cli.command(name="overlay-key-status")
@click.pass_obj
def overlay_key_status(cli_ctx: CLIContext) -> None:
    """Show overlay root metadata without exposing key material."""
    from ai.backend.manager.cli.context import etcd_ctx

    async def _impl() -> None:
        async with etcd_ctx(cli_ctx) as etcd:
            status = await overlay_encryption_key_status(etcd)
        click.echo(f"active-key-id: {status.active_key_id}")
        click.echo(f"activated-at: {_display_timestamp(status.activated_at)}")
        click.echo(f"retired-key-count: {len(status.retired_key_ids)}")

    asyncio.run(_impl())


@cli.command(name="rotate-overlay-key")
@click.option(
    "--confirm-drained",
    is_flag=True,
    help="Confirm that all managers using older releases are stopped and sessions are drained.",
)
@click.pass_obj
def rotate_overlay_key(cli_ctx: CLIContext, confirm_drained: bool) -> None:
    """Rotate the overlay root after a full encrypted-session drain."""
    from ai.backend.manager.cli.context import etcd_ctx

    if not confirm_drained:
        raise click.UsageError("--confirm-drained is required")

    async def _impl() -> None:
        async with etcd_ctx(cli_ctx) as etcd:
            status = await rotate_overlay_encryption_key(etcd)
        click.echo(f"active-key-id: {status.active_key_id}")
        click.echo(f"activated-at: {_display_timestamp(status.activated_at)}")

    asyncio.run(_impl())


@cli.command(name="audit")
@click.option(
    "--repair",
    is_flag=True,
    help="Run the CAS-guarded reconciler once before producing the audit report.",
)
@click.pass_obj
def audit(cli_ctx: CLIContext, repair: bool) -> None:
    """Report invalid and orphaned cluster-network records without exposing values."""
    from ai.backend.manager.cli.context import config_provider_ctx, etcd_ctx
    from ai.backend.manager.network.diagnostics import audit_overlay_state, repair_overlay_state

    async def _impl() -> None:
        async with (
            etcd_ctx(cli_ctx) as etcd,
            config_provider_ctx(cli_ctx) as config_provider,
        ):
            config = config_provider.config.network.inter_container
            reclaimed = 0
            if repair:
                reclaimed = await repair_overlay_state(
                    etcd,
                    pool=config.ipam_pool,
                    block_prefixlen=config.ipam_block_size,
                )
            report = await audit_overlay_state(etcd)
        click.echo(
            json.dumps(
                {
                    "healthy": report.healthy,
                    "reclaimed": reclaimed,
                    "session_records": report.session_records,
                    "pool_claims": report.pool_claims,
                    "session_child_records": report.session_child_records,
                    "invalid_records": report.invalid_records,
                    "orphan_claims": report.orphan_claims,
                    "orphan_session_children": report.orphan_session_children,
                    "samples": report.samples,
                },
                indent=2,
                sort_keys=True,
            )
        )
        if not report.healthy:
            raise click.exceptions.Exit(2)

    asyncio.run(_impl())


@cli.command(name="quarantine")
@click.argument("key")
@click.option(
    "--confirm-orphaned",
    is_flag=True,
    help="Confirm that the exact key is not owned by a live session.",
)
@click.pass_obj
def quarantine(cli_ctx: CLIContext, key: str, confirm_orphaned: bool) -> None:
    """Move one confirmed orphan to a guarded quarantine record."""
    from ai.backend.manager.cli.context import etcd_ctx
    from ai.backend.manager.network.diagnostics import quarantine_overlay_record

    if not confirm_orphaned:
        raise click.UsageError("--confirm-orphaned is required")

    async def _impl() -> None:
        async with etcd_ctx(cli_ctx) as etcd:
            destination = await quarantine_overlay_record(etcd, key)
        click.echo(destination)

    asyncio.run(_impl())
