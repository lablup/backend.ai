"""User-facing CLI: ``./bai deployment chat-config`` (manage local chat cache)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
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
        raise click.ClickException(f"{status}: {detail}") from e


@click.group(name="chat-config")
def chat_config() -> None:
    """Manage stored API keys and discovered model names for deployment chat.

    The deployment's ``endpoint_url`` and the served model name are
    resolved automatically (from the manager and the inference endpoint
    respectively); only the API key is registered through this command.
    """


@chat_config.command(name="set")
@click.argument("deployment_id", type=click.UUID)
@click.option(
    "--token",
    "api_key",
    default=None,
    type=str,
    help=(
        "API key the inference runtime accepts as a Bearer token. "
        "Omit when the runtime was started without an API key."
    ),
)
@click.option(
    "--no-token",
    is_flag=True,
    default=False,
    help="Explicitly clear the cached API key (deployment exposes no auth).",
)
@click.option(
    "--default-model",
    default=None,
    type=str,
    help=(
        "Override the auto-discovered served model name. "
        "If omitted, the model is fetched from the inference endpoint's /v1/models."
    ),
)
def set_(
    deployment_id: UUID,
    api_key: str | None,
    no_token: bool,
    default_model: str | None,
) -> None:
    """Register or update the chat cache entry for a deployment."""
    if api_key and no_token:
        raise click.ClickException("--token and --no-token are mutually exclusive.")

    config = load_v2_config()
    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        raise click.ClickException(str(e)) from e

    existing = cache.get(deployment_id)
    resolved_key: str | None
    if no_token:
        resolved_key = None
    elif api_key is not None:
        resolved_key = api_key
    else:
        resolved_key = cache.get_token(deployment_id)

    async def _run() -> None:
        registry = await create_v2_registry(config)
        try:
            deployment = await registry.deployment.get(deployment_id)
        finally:
            await registry.close()
        endpoint_url = deployment.network_access.endpoint_url
        if not endpoint_url:
            raise click.ClickException(
                f"Deployment {deployment_id} has no endpoint_url yet "
                "(it may still be provisioning). Wait until the deployment is READY."
            )

        if default_model is not None:
            served_model: str | None = default_model
        else:
            served_model = await _discover_model(
                endpoint_url,
                resolved_key,
                config.skip_ssl_verification,
                existing.default_model if existing is not None else None,
            )

        cache.upsert(
            deployment_id,
            DeploymentChatCacheEntry(
                endpoint_url=endpoint_url,
                default_model=served_model,
                last_synced_at=datetime.now(UTC),
            ),
        )
        if resolved_key is None:
            cache.clear_token(deployment_id)
        else:
            cache.set_token(deployment_id, resolved_key)
        save_chat_cache(cache)
        click.echo(f"Updated chat cache entry for deployment {deployment_id}.")
        if served_model:
            click.echo(f"  default_model: {served_model}")
        click.echo(f"  api_key:       {mask_token(resolved_key)}")

    _run_async(_run)


async def _discover_model(
    endpoint_url: str,
    api_key: str | None,
    skip_ssl_verification: bool,
    fallback: str | None,
) -> str | None:
    """Call ``GET {endpoint}/v1/models`` to learn the served model name.

    Returns the first model id reported by the inference endpoint. Falls
    back to *fallback* when the endpoint is unreachable or the response
    does not contain any model entries.
    """
    from ai.backend.client.exceptions import BackendAPIError, BackendClientError
    from ai.backend.client.v2.deployment_chat import (
        DeploymentChatAuthError,
        DeploymentChatClient,
    )

    async with DeploymentChatClient(skip_ssl_verification=skip_ssl_verification) as client:
        try:
            payload = await client.list_models(endpoint_url, api_key)
        except (DeploymentChatAuthError, BackendAPIError, BackendClientError):
            return fallback
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return fallback
    for entry in data:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            return str(entry["id"])
    return fallback


@chat_config.command(name="show")
@click.argument("deployment_id", type=click.UUID, required=False)
def show(deployment_id: UUID | None) -> None:
    """Print one or all chat cache entries (API keys are masked)."""
    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        raise click.ClickException(str(e)) from e

    if deployment_id is not None:
        entry = cache.get(deployment_id)
        token = cache.get_token(deployment_id)
        if entry is None and token is None:
            raise click.ClickException(f"No chat cache entry for deployment {deployment_id}.")
        _print_entry(deployment_id, entry, token)
        return

    dep_ids = set(cache.entries) | set(cache.tokens)
    if not dep_ids:
        click.echo("No chat cache entries.")
        return
    for dep_id in dep_ids:
        _print_entry(dep_id, cache.get(dep_id), cache.get_token(dep_id))
        click.echo("")


@chat_config.command(name="clear")
@click.argument("deployment_id", type=click.UUID)
def clear(deployment_id: UUID) -> None:
    """Remove the chat cache entry and stored token for a deployment."""
    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        raise click.ClickException(str(e)) from e
    if cache.remove(deployment_id):
        save_chat_cache(cache)
        click.echo(f"Removed chat cache entry for deployment {deployment_id}.")
    else:
        click.echo(f"No chat cache entry for deployment {deployment_id}.")


def _print_entry(
    deployment_id: UUID,
    entry: DeploymentChatCacheEntry | None,
    token: str | None,
) -> None:
    click.echo(f"deployment_id : {deployment_id}")
    click.echo(f"endpoint_url  : {entry.endpoint_url if entry else '-'}")
    click.echo(f"api_key       : {mask_token(token)}")
    click.echo(f"default_model : {(entry.default_model if entry else None) or '-'}")
    click.echo(f"last_synced_at: {entry.last_synced_at.isoformat() if entry else '-'}")


__all__ = ("chat_config",)
