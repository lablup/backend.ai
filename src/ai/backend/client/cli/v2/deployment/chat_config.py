"""User-facing CLI: ``./bai deployment chat-config`` (manage local chat cache)."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, NoReturn
from uuid import UUID

import click

from ai.backend.client.cli.v2.deployment_chat_cache import (
    DeploymentChatCacheEntry,
    IncompatibleChatCacheError,
    load_chat_cache,
    mask_token,
    save_chat_cache,
)
from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config


def _abort(message: str) -> NoReturn:
    click.echo(message, err=True)
    sys.exit(1)


def _run_async(coro_fn: Callable[[], Awaitable[None]]) -> None:
    from ai.backend.client.exceptions import BackendAPIError

    try:
        asyncio.run(coro_fn())
    except BackendAPIError as e:
        data: Any = e.args[2] if len(e.args) > 2 else {}
        title = data.get("title", "") if isinstance(data, dict) else ""
        msg = data.get("msg", "") if isinstance(data, dict) else ""
        status = e.args[0] if e.args else "?"
        detail = title or msg or str(e)
        click.echo(f"Error ({status}): {detail}", err=True)
        sys.exit(1)


@click.group(name="chat-config")
def chat_config() -> None:
    """Manage stored vLLM API keys for deployment chat.

    The deployment's ``endpoint_url`` is always resolved from the manager
    automatically; only the API key is registered through this command.
    """


@chat_config.command(name="set")
@click.argument("deployment_id", type=click.UUID)
@click.option(
    "--token",
    "vllm_api_key",
    required=True,
    type=str,
    help="The vLLM API key the deployment was started with (--api-key).",
)
@click.option(
    "--default-model",
    default=None,
    type=str,
    help="Default model name sent with chat requests when --model is omitted.",
)
def set_(
    deployment_id: UUID,
    vllm_api_key: str,
    default_model: str | None,
) -> None:
    """Register or update the vLLM API key for a deployment.

    The deployment's endpoint URL is resolved from the manager and stored
    alongside the key so the next ``chat`` invocation does not need to
    re-query.
    """
    config = load_v2_config()
    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        _abort(str(e))

    existing = cache.get(deployment_id)

    async def _run() -> None:
        registry = await create_v2_registry(config)
        try:
            deployment = await registry.deployment.get(deployment_id)
        finally:
            await registry.close()
        resolved = deployment.network_access.endpoint_url
        if not resolved:
            raise click.ClickException(
                f"Deployment {deployment_id} has no endpoint_url yet "
                "(it may still be provisioning). Wait until the deployment is READY."
            )

        cache.upsert(
            deployment_id,
            DeploymentChatCacheEntry(
                endpoint_url=resolved,
                vllm_api_key=vllm_api_key,
                default_model=(
                    default_model
                    if default_model is not None
                    else (existing.default_model if existing is not None else None)
                ),
                last_synced_at=datetime.now(UTC),
            ),
        )
        save_chat_cache(cache)
        click.echo(f"Updated chat cache entry for deployment {deployment_id}.")

    _run_async(_run)


@chat_config.command(name="show")
@click.argument("deployment_id", type=click.UUID, required=False)
def show(deployment_id: UUID | None) -> None:
    """Print one or all chat cache entries (API keys are masked)."""
    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        _abort(str(e))

    if deployment_id is not None:
        entry = cache.get(deployment_id)
        if entry is None:
            _abort(f"No chat cache entry for deployment {deployment_id}.")
        else:
            _print_entry(deployment_id, entry)
        return

    if not cache.entries:
        click.echo("No chat cache entries.")
        return
    for dep_id, entry in cache.entries.items():
        _print_entry(dep_id, entry)
        click.echo("")


@chat_config.command(name="clear")
@click.argument("deployment_id", type=click.UUID)
def clear(deployment_id: UUID) -> None:
    """Remove the chat cache entry for a deployment."""
    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        _abort(str(e))
    if cache.remove(deployment_id):
        save_chat_cache(cache)
        click.echo(f"Removed chat cache entry for deployment {deployment_id}.")
    else:
        click.echo(f"No chat cache entry for deployment {deployment_id}.")


def _print_entry(deployment_id: UUID, entry: DeploymentChatCacheEntry) -> None:
    click.echo(f"deployment_id : {deployment_id}")
    click.echo(f"endpoint_url  : {entry.endpoint_url}")
    click.echo(f"vllm_api_key  : {mask_token(entry.vllm_api_key)}")
    click.echo(f"default_model : {entry.default_model or '-'}")
    click.echo(f"last_synced_at: {entry.last_synced_at.isoformat()}")


__all__ = ("chat_config",)
