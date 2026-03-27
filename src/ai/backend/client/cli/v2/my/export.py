"""Self-service export CLI commands."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config


@click.group()
def export() -> None:
    """Export my data as CSV."""


@export.command(name="sessions")
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def my_sessions(output: str | None, fields: str | None, encoding: str) -> None:
    """Export my sessions as CSV."""
    from ai.backend.common.dto.manager.v2.export import SessionExportCSVInput

    field_list = [f.strip() for f in fields.split(",")] if fields else None
    body = SessionExportCSVInput(fields=field_list, encoding=encoding)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            data = await registry.export.download_my_sessions_csv(body)
            _write_output(data, output)
        finally:
            await registry.close()

    asyncio.run(_run())


@export.command(name="keypairs")
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def my_keypairs(output: str | None, fields: str | None, encoding: str) -> None:
    """Export my keypairs as CSV."""
    from ai.backend.common.dto.manager.v2.export import KeypairExportCSVInput

    field_list = [f.strip() for f in fields.split(",")] if fields else None
    body = KeypairExportCSVInput(fields=field_list, encoding=encoding)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            data = await registry.export.download_my_keypairs_csv(body)
            _write_output(data, output)
        finally:
            await registry.close()

    asyncio.run(_run())


def _write_output(data: bytes, output: str | None) -> None:
    """Write CSV data to file or stdout."""
    if output:
        Path(output).write_bytes(data)
        click.echo(f"Exported to {output}")
    else:
        sys.stdout.buffer.write(data)
