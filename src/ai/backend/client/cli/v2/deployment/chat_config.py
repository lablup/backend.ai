"""User-facing CLI: ``./bai deployment chat-config`` (manage local chat cache)."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from typing import NoReturn
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


@click.group(name="chat-config")
def chat_config() -> None:
    """Manage local chat cache for deployment chat (vLLM API keys, endpoints)."""


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
    "--endpoint-url",
    default=None,
    type=str,
    help="Override the deployment's endpoint_url (otherwise auto-resolved).",
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
    endpoint_url: str | None,
    default_model: str | None,
) -> None:
    """Register or update the chat cache entry for a deployment."""
    config = load_v2_config()
    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        _abort(str(e))

    existing = cache.get(deployment_id)

    async def _resolve() -> str:
        if endpoint_url:
            return endpoint_url
        if existing is not None and existing.endpoint_url:
            return existing.endpoint_url
        registry = await create_v2_registry(config)
        try:
            deployment = await registry.deployment.get(deployment_id)
        finally:
            await registry.close()
        resolved = deployment.network_access.endpoint_url
        if not resolved:
            raise click.ClickException(
                f"Deployment {deployment_id} has no endpoint_url yet "
                "(it may still be provisioning). Provide --endpoint-url explicitly."
            )
        return resolved

    final_endpoint = asyncio.run(_resolve())

    cache.upsert(
        deployment_id,
        DeploymentChatCacheEntry(
            endpoint_url=final_endpoint,
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
