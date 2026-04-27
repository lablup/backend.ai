"""User-facing CLI: ``./bai deployment chat`` (one-shot OpenAI-compatible chat)."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING, NoReturn
from uuid import UUID

import click

from ai.backend.client.cli.v2.deployment_chat_cache import (
    CHAT_CACHE_FILE,
    DeploymentChatCacheEntry,
    IncompatibleChatCacheError,
    load_chat_cache,
    save_chat_cache,
)
from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result

if TYPE_CHECKING:
    from ai.backend.client.v2.v2_registry import V2ClientRegistry


def _abort(message: str) -> NoReturn:
    click.echo(message, err=True)
    sys.exit(1)


async def _resolve_endpoint_url(registry: V2ClientRegistry, deployment_id: UUID) -> str:
    deployment = await registry.deployment.get(deployment_id)
    endpoint_url = deployment.network_access.endpoint_url
    if not endpoint_url:
        raise click.ClickException(
            f"Deployment {deployment_id} has no endpoint_url yet "
            "(it may still be provisioning). Wait until the deployment is ACTIVE."
        )
    return endpoint_url


@click.command(name="chat")
@click.argument("deployment_id", type=click.UUID)
@click.argument("content", type=str)
@click.option(
    "--model",
    default=None,
    type=str,
    help="Model name to send (defaults to cached default_model or 'default').",
)
@click.option(
    "--temperature",
    default=None,
    type=float,
    help="Sampling temperature.",
)
@click.option(
    "--max-tokens",
    default=None,
    type=int,
    help="Maximum number of tokens to generate.",
)
def chat(
    deployment_id: UUID,
    content: str,
    model: str | None,
    temperature: float | None,
    max_tokens: int | None,
) -> None:
    """Send a one-shot chat completion request to a deployed vLLM model."""
    from ai.backend.client.exceptions import BackendAPIError
    from ai.backend.client.v2.chat_dto import ChatCompletionRequest, ChatMessage
    from ai.backend.client.v2.domains_v2.deployment_chat import (
        DeploymentChatAuthError,
        DeploymentChatClient,
    )

    config = load_v2_config()

    try:
        cache = load_chat_cache()
    except IncompatibleChatCacheError as e:
        _abort(str(e))

    entry = cache.get(deployment_id)

    async def _ensure_endpoint() -> DeploymentChatCacheEntry:
        if entry is not None and entry.endpoint_url:
            return entry
        registry = await create_v2_registry(config)
        try:
            endpoint_url = await _resolve_endpoint_url(registry, deployment_id)
        finally:
            await registry.close()
        new_entry = DeploymentChatCacheEntry(
            endpoint_url=endpoint_url,
            vllm_api_key=entry.vllm_api_key if entry is not None else None,
            default_model=entry.default_model if entry is not None else None,
            last_synced_at=datetime.now(UTC),
        )
        cache.upsert(deployment_id, new_entry)
        save_chat_cache(cache)
        return new_entry

    async def _run() -> None:
        resolved = await _ensure_endpoint()
        if resolved.vllm_api_key is None:
            _abort(
                f"No vLLM API key registered for deployment {deployment_id}.\n"
                "Register one with:\n"
                f"  ./bai deployment chat-config set {deployment_id} --token <vllm_api_key>"
            )

        request_model = model or resolved.default_model or "default"
        chat_request = ChatCompletionRequest(
            model=request_model,
            messages=[ChatMessage(role="user", content=content)],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        async with DeploymentChatClient(
            skip_ssl_verification=config.skip_ssl_verification,
        ) as chat_client:
            try:
                response = await chat_client.chat_completion(
                    resolved.endpoint_url,
                    resolved.vllm_api_key,
                    chat_request,
                )
            except DeploymentChatAuthError:
                invalidated = DeploymentChatCacheEntry(
                    endpoint_url=resolved.endpoint_url,
                    vllm_api_key=None,
                    default_model=resolved.default_model,
                    last_synced_at=datetime.now(UTC),
                )
                cache.upsert(deployment_id, invalidated)
                save_chat_cache(cache)
                _abort(
                    f"The inference endpoint rejected the configured API key for "
                    f"deployment {deployment_id}. The cached key has been cleared.\n"
                    "Register a new one with:\n"
                    f"  ./bai deployment chat-config set {deployment_id} --token <vllm_api_key>"
                )
            except BackendAPIError as e:
                _abort(f"Inference endpoint error ({e.status} {e.reason}): {e.data}")
        print_result(response)

    asyncio.run(_run())


__all__ = ("chat", "CHAT_CACHE_FILE")
