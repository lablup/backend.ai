"""User-facing CLI commands for deployment access tokens."""

from __future__ import annotations

import asyncio
import sys
import uuid
from typing import Any

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


def _run_async(coro_fn: Any) -> None:
    from ai.backend.client.exceptions import BackendAPIError

    try:
        asyncio.run(coro_fn())
    except BackendAPIError as e:
        data = e.args[2] if len(e.args) > 2 else {}
        title = data.get("title", "") if isinstance(data, dict) else ""
        msg = data.get("msg", "") if isinstance(data, dict) else ""
        status = e.args[0] if e.args else "?"
        detail = title or msg or str(e)
        click.echo(f"Error ({status}): {detail}", err=True)
        sys.exit(1)


@click.group(name="access-token")
def access_token() -> None:
    """Deployment access token commands."""


@access_token.command()
@click.argument("deployment_id", type=click.UUID)
@click.option(
    "--expires-at",
    default=None,
    type=click.DateTime(),
    help="Token expiration timestamp (ISO8601 format).",
)
def create(deployment_id: uuid.UUID, expires_at: Any) -> None:
    """Create an access token for a deployment."""
    from datetime import datetime

    from ai.backend.common.dto.manager.v2.deployment.request import CreateAccessTokenInput

    body = CreateAccessTokenInput(
        deployment_id=deployment_id,
        expires_at=datetime.fromisoformat(expires_at.isoformat()) if expires_at else None,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.create_access_token(deployment_id, body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@access_token.command()
@click.argument("token_id", type=click.UUID)
def get(token_id: uuid.UUID) -> None:
    """Get an access token by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.get_access_token(token_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@access_token.command()
@click.argument("token_id", type=click.UUID)
def delete(token_id: uuid.UUID) -> None:
    """Delete an access token."""
    from ai.backend.common.dto.manager.v2.deployment.request import DeleteAccessTokenInput

    body = DeleteAccessTokenInput(id=token_id)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.delete_access_token(body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@access_token.command(name="bulk-delete")
@click.argument("token_ids", nargs=-1, required=True, type=click.UUID)
def bulk_delete(token_ids: tuple[uuid.UUID, ...]) -> None:
    """Bulk delete access tokens."""
    from ai.backend.common.dto.manager.v2.deployment.request import BulkDeleteAccessTokensInput

    body = BulkDeleteAccessTokensInput(ids=list(token_ids))

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.bulk_delete_access_tokens(body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@access_token.command()
@click.argument("deployment_id", type=click.UUID)
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
def search(deployment_id: uuid.UUID, limit: int, offset: int) -> None:
    """Search access tokens for a deployment."""
    from ai.backend.common.dto.manager.v2.deployment.request import SearchAccessTokensInput

    body = SearchAccessTokensInput(
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.search_access_tokens(deployment_id, body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
