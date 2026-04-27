"""User-facing CLI: ``./bai deployment chat`` (one-shot OpenAI-compatible chat)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import click

from ai.backend.client.cli.v2.deployment_chat_cache import (
    CHAT_CACHE_FILE,
    DeploymentChatCacheEntry,
    IncompatibleChatCacheError,
    load_chat_cache,
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
    "--temperature",
    default=None,
    type=click.FloatRange(min=0.0, max=2.0),
    help="Sampling temperature.",
)
@click.option(
    "--top-p",
    default=None,
    type=click.FloatRange(min=0.0, max=1.0),
    help="Nucleus sampling probability mass.",
)
@click.option(
    "--frequency-penalty",
    default=None,
    type=click.FloatRange(min=-2.0, max=2.0),
    help="Penalty for token frequency.",
)
@click.option(
    "--presence-penalty",
    default=None,
    type=click.FloatRange(min=-2.0, max=2.0),
    help="Penalty for token presence.",
)
@click.option(
    "--seed",
    default=None,
    type=int,
    help="Random seed for deterministic sampling.",
)
@click.option(
    "--stop",
    multiple=True,
    type=str,
    help="Stop sequence (repeatable).",
)
@click.option(
    "--max-tokens",
    default=None,
    type=click.IntRange(min=1),
    help="Maximum number of tokens to generate.",
)
def chat(
    deployment_id: UUID,
    content: str,
    model: str | None,
    temperature: float | None,
    top_p: float | None,
    frequency_penalty: float | None,
    presence_penalty: float | None,
    seed: int | None,
    stop: tuple[str, ...],
    max_tokens: int | None,
) -> None:
    """Send a one-shot chat completion request to a deployed model."""
    import json
    import sys

    from ai.backend.client.v2.domains_v2.inference_chat import (
        InferenceChatAuthError,
        InferenceChatClient,
    )

    config = load_v2_config()

    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        raise click.ClickException(str(e)) from e

    entry = cache.get(deployment_id)

    async def _resolve_endpoint() -> DeploymentChatCacheEntry:
        if entry is not None and entry.endpoint_url:
            return entry
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
        new_entry = DeploymentChatCacheEntry(
            endpoint_url=endpoint_url,
            api_key=entry.api_key if entry is not None else None,
            default_model=entry.default_model if entry is not None else None,
            last_synced_at=datetime.now(UTC),
        )
        cache.upsert(deployment_id, new_entry)
        save_chat_cache(cache)
        return new_entry

    def _build_request_body(model_name: str) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model_name,
            "messages": [{"role": "user", "content": content}],
        }
        if temperature is not None:
            body["temperature"] = temperature
        if top_p is not None:
            body["top_p"] = top_p
        if frequency_penalty is not None:
            body["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            body["presence_penalty"] = presence_penalty
        if seed is not None:
            body["seed"] = seed
        if stop:
            body["stop"] = list(stop)
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        return body

    async def _run() -> None:
        from ai.backend.client.exceptions import BackendAPIError

        resolved = await _resolve_endpoint()
        request_model = model or resolved.default_model
        if request_model is None:
            raise click.ClickException(
                f"No --model given and no default_model cached for deployment {deployment_id}.\n"
                "Set one with:\n"
                f"  ./bai deployment chat-config set {deployment_id} --token <api_key>\n"
                "(this auto-discovers the served model from the inference endpoint)."
            )

        body = _build_request_body(request_model)
        async with InferenceChatClient(
            skip_ssl_verification=config.skip_ssl_verification,
        ) as client:
            try:
                response = await client.chat_completion(
                    resolved.endpoint_url,
                    resolved.api_key,
                    body,
                )
            except InferenceChatAuthError as e:
                invalidated = DeploymentChatCacheEntry(
                    endpoint_url=resolved.endpoint_url,
                    api_key=None,
                    default_model=resolved.default_model,
                    last_synced_at=datetime.now(UTC),
                )
                cache.upsert(deployment_id, invalidated)
                save_chat_cache(cache)
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
