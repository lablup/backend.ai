"""Admin CLI commands for v2 export API."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def export() -> None:
    """CSV export administration commands."""


@export.command(name="list-reports")
def list_reports() -> None:
    """List all available export reports."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.export.list_reports()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@export.command(name="get-report")
@click.argument("report_key", type=str)
def get_report(report_key: str) -> None:
    """Get details of a specific export report."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.export.get_report(report_key)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@export.command(name="users")
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_users(output: str | None, fields: str | None, encoding: str) -> None:
    """Export users as CSV."""
    from ai.backend.common.dto.manager.v2.export import UserExportCSVInput

    field_list = [f.strip() for f in fields.split(",")] if fields else None
    body = UserExportCSVInput(fields=field_list, encoding=encoding)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            data = await registry.export.download_users_csv(body)
            _write_output(data, output)
        finally:
            await registry.close()

    asyncio.run(_run())


@export.command(name="sessions")
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_sessions(output: str | None, fields: str | None, encoding: str) -> None:
    """Export sessions as CSV."""
    from ai.backend.common.dto.manager.v2.export import SessionExportCSVInput

    field_list = [f.strip() for f in fields.split(",")] if fields else None
    body = SessionExportCSVInput(fields=field_list, encoding=encoding)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            data = await registry.export.download_sessions_csv(body)
            _write_output(data, output)
        finally:
            await registry.close()

    asyncio.run(_run())


@export.command(name="projects")
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_projects(output: str | None, fields: str | None, encoding: str) -> None:
    """Export projects as CSV."""
    from ai.backend.common.dto.manager.v2.export import ProjectExportCSVInput

    field_list = [f.strip() for f in fields.split(",")] if fields else None
    body = ProjectExportCSVInput(fields=field_list, encoding=encoding)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            data = await registry.export.download_projects_csv(body)
            _write_output(data, output)
        finally:
            await registry.close()

    asyncio.run(_run())


@export.command(name="keypairs")
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_keypairs(output: str | None, fields: str | None, encoding: str) -> None:
    """Export keypairs as CSV."""
    from ai.backend.common.dto.manager.v2.export import KeypairExportCSVInput

    field_list = [f.strip() for f in fields.split(",")] if fields else None
    body = KeypairExportCSVInput(fields=field_list, encoding=encoding)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            data = await registry.export.download_keypairs_csv(body)
            _write_output(data, output)
        finally:
            await registry.close()

    asyncio.run(_run())


@export.command(name="audit-logs")
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_audit_logs(output: str | None, fields: str | None, encoding: str) -> None:
    """Export audit logs as CSV."""
    from ai.backend.common.dto.manager.v2.export import AuditLogExportCSVInput

    field_list = [f.strip() for f in fields.split(",")] if fields else None
    body = AuditLogExportCSVInput(fields=field_list, encoding=encoding)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            data = await registry.export.download_audit_logs_csv(body)
            _write_output(data, output)
        finally:
            await registry.close()

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Scoped export commands
# ---------------------------------------------------------------------------


@export.command(name="sessions-by-project")
@click.argument("project_id", type=str)
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_sessions_by_project(
    project_id: str, output: str | None, fields: str | None, encoding: str
) -> None:
    """Export sessions within a project as CSV."""
    from ai.backend.common.dto.manager.v2.export import SessionExportCSVInput

    field_list = [f.strip() for f in fields.split(",")] if fields else None
    body = SessionExportCSVInput(fields=field_list, encoding=encoding)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            data = await registry.export.download_sessions_by_project_csv(UUID(project_id), body)
            _write_output(data, output)
        finally:
            await registry.close()

    asyncio.run(_run())


@export.command(name="users-by-domain")
@click.argument("domain_name", type=str)
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_users_by_domain(
    domain_name: str, output: str | None, fields: str | None, encoding: str
) -> None:
    """Export users within a domain as CSV."""
    from ai.backend.common.dto.manager.v2.export import UserExportCSVInput

    field_list = [f.strip() for f in fields.split(",")] if fields else None
    body = UserExportCSVInput(fields=field_list, encoding=encoding)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            data = await registry.export.download_users_by_domain_csv(domain_name, body)
            _write_output(data, output)
        finally:
            await registry.close()

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _write_output(data: bytes, output: str | None) -> None:
    """Write CSV data to file or stdout."""
    if output:
        Path(output).write_bytes(data)
        click.echo(f"Exported to {output}")
    else:
        sys.stdout.buffer.write(data)
