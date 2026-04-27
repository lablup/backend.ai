"""User-facing CLI: ``./bai deployment chat`` (one-shot OpenAI-compatible chat)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import click

from ai.backend.cli.params import JSONParamType
from ai.backend.client.cli.v2.deployment_chat_cache import (
    CHAT_CACHE_FILE,
    DeploymentChatCacheEntry,
    IncompatibleChatCacheError,
    load_chat_cache,
    save_chat_cache,
)
from ai.backend.client.cli.v2.deployment_chat_config import (
    IncompatibleChatConfigError,
    load_chat_config,
    save_chat_config,
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


@click.command(name="chat")
@click.argument("deployment_id", type=click.UUID)
@click.argument("content", type=str)
@click.option(
    "--model",
    default=None,
    type=str,
    help="Model name to send (defaults to cached default_model).",
)
@click.option(
    "--params",
    default="{}",
    type=JSONParamType(),
    help=(
        "Extra request-body fields as a JSON object. "
        "Forwarded to the inference endpoint as-is "
        '(e.g. \'{"temperature": 0.7, "max_tokens": 256}\'). '
        "The 'model' and 'messages' fields are always overridden by --model and CONTENT."
    ),
)
def chat(
    deployment_id: UUID,
    content: str,
    model: str | None,
    params: Any,
) -> None:
    """Send a one-shot chat completion request to a deployed model.

    Sampling parameters (temperature, top_p, max_tokens, etc.) are not
    exposed as individual flags because their schema differs across
    runtime variants. Pass them through ``--params`` instead.
    """
    import json
    import sys

    from ai.backend.client.v2.deployment_chat import (
        DeploymentChatAuthError,
        DeploymentChatClient,
    )

    connection = load_v2_config()

    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        raise click.ClickException(str(e)) from e
    try:
        chat_config = load_chat_config()
    except IncompatibleChatConfigError as e:
        raise click.ClickException(str(e)) from e

    if not isinstance(params, dict):
        raise click.ClickException("--params must be a JSON object.")
    extra_body: dict[str, Any] = params
    entry = cache.get(deployment_id)

    async def _ensure_endpoint_entry() -> DeploymentChatCacheEntry:
        if entry is not None and entry.endpoint_url:
            return entry
        registry = await create_v2_registry(connection)
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
        new_entry = DeploymentChatCacheEntry(
            endpoint_url=endpoint_url,
            default_model=entry.default_model if entry is not None else None,
            last_synced_at=datetime.now(UTC),
        )
        cache.upsert(deployment_id, new_entry)
        save_chat_cache(cache)
        return new_entry

    async def _run() -> None:
        from ai.backend.client.exceptions import BackendAPIError

        endpoint_entry = await _ensure_endpoint_entry()
        request_model = model or endpoint_entry.default_model
        if request_model is None:
            raise click.ClickException(
                f"No --model given and no default_model cached for deployment {deployment_id}.\n"
                "Set one with:\n"
                f"  ./bai deployment chat-config set {deployment_id} --token <api_key>\n"
                "(this auto-discovers the served model from the inference endpoint)."
            )

        body: dict[str, Any] = {
            **extra_body,
            "model": request_model,
            "messages": [{"role": "user", "content": content}],
        }
        api_key = chat_config.get_token(deployment_id)
        async with DeploymentChatClient(
            skip_ssl_verification=connection.skip_ssl_verification,
        ) as client:
            try:
                response = await client.chat_completion(
                    endpoint_entry.endpoint_url,
                    api_key,
                    body,
                )
            except DeploymentChatAuthError as e:
                chat_config.clear_token(deployment_id)
                save_chat_config(chat_config)
                raise click.ClickException(
                    f"The inference endpoint rejected the configured API key for "
                    f"deployment {deployment_id}. The cached key has been cleared.\n"
                    "Register a new one with:\n"
                    f"  ./bai deployment chat-config set {deployment_id} --token <api_key>"
                ) from e
            except BackendAPIError as e:
                raise click.ClickException(
                    f"Inference endpoint error ({e.status} {e.reason}): {e.data}"
                ) from e
        sys.stdout.write(json.dumps(response, indent=2, ensure_ascii=False, default=str) + "\n")

    _run_async(_run)


__all__ = ("chat", "CHAT_CACHE_FILE")
