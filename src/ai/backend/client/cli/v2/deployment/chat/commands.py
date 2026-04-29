"""User-facing CLI: ``./bai deployment chat`` and ``chat-config``."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import click

from ai.backend.cli.params import JSONParamType
from ai.backend.client.cli.v2.deployment.chat.formatter import (
    DeploymentChatFormatter,
    mask_token,
)
from ai.backend.client.cli.v2.deployment.chat.types import (
    ChatCompletionRequest,
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    DeploymentChatConfig,
)
from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config


def _run_async(coro_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
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


# ---------------------------------------------------------------------------
# chat
# ---------------------------------------------------------------------------


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

    Targets OpenAI-compatible Chat Completions endpoints
    (vLLM / SGLang / NIM / TGI in messages-api mode / custom containers
    that follow the same contract). Sampling parameters such as
    temperature and top_p differ between runtime variants — pass them
    through ``--params``.
    """
    import json

    from ai.backend.client.v2.config import ClientConfig
    from ai.backend.client.v2.deployment_chat import DeploymentChatClient
    from ai.backend.client.v2.exceptions import DeploymentAuthError

    connection_config = load_v2_config()

    cache = DeploymentChatCache.load()
    chat_config = DeploymentChatConfig.load()

    if not isinstance(params, dict):
        raise click.ClickException("--params must be a JSON object.")
    extra_body: dict[str, Any] = params

    async def _run() -> None:
        from ai.backend.client.exceptions import BackendAPIError

        existing = cache.get(deployment_id)
        if existing is not None and not existing.is_expired(now=datetime.now(UTC)):
            endpoint_entry = existing
        else:
            registry = await create_v2_registry(connection_config)
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
            endpoint_entry = DeploymentChatCacheEntry(
                endpoint_url=endpoint_url,
                default_model=existing.default_model if existing is not None else None,
                last_synced_at=datetime.now(UTC),
            )
            cache.set(deployment_id, endpoint_entry)
            cache.save()

        request_model = model or endpoint_entry.default_model
        if request_model is None:
            raise click.ClickException(
                f"No --model given and no default_model cached for deployment {deployment_id}.\n"
                "Set one with:\n"
                f"  ./bai deployment chat-config set {deployment_id} --default-model <name>"
            )

        request = ChatCompletionRequest.model_validate({
            **extra_body,
            "model": request_model,
            "messages": [{"role": "user", "content": content}],
        })
        body = request.model_dump(mode="json")
        token = chat_config.get_token(deployment_id)
        # ``endpoint`` is required on ClientConfig but unused by AppProxyClient
        # (deployment URLs are passed per-request); pass through the manager
        # endpoint so the rest of the connection knobs (TLS, timeouts) match.
        client_config = ClientConfig(
            endpoint=connection_config.endpoint,
            endpoint_type=connection_config.endpoint_type,
            api_version=connection_config.api_version,
            skip_ssl_verification=connection_config.skip_ssl_verification,
        )
        async with DeploymentChatClient(client_config) as client:
            try:
                response = await client.chat_completion(
                    endpoint_entry.endpoint_url,
                    token,
                    body,
                )
            except DeploymentAuthError as e:
                # 401/403: invalidate the cached token so the next ``chat`` call
                # surfaces the same hint instead of silently re-sending a stale key.
                if token is not None and chat_config.pop_token(deployment_id):
                    chat_config.save()
                raise click.ClickException(
                    f"The inference endpoint rejected the configured token for "
                    f"deployment {deployment_id}. The cached token has been cleared; "
                    f"re-register with:\n"
                    f"  ./bai deployment chat-config set {deployment_id} --token <token>"
                ) from e
            except BackendAPIError as e:
                raise click.ClickException(
                    f"Inference endpoint error ({e.status} {e.reason}): {e.data}"
                ) from e
        print(json.dumps(response, indent=2, ensure_ascii=False, default=str))

    _run_async(_run)


# ---------------------------------------------------------------------------
# chat-config
# ---------------------------------------------------------------------------


@click.group(name="chat-config")
def chat_config() -> None:
    """Manage stored tokens and default model names for deployment chat.

    The deployment's ``endpoint_url`` is auto-managed; ``--token`` and
    ``--default-model`` are user-supplied.
    """


@chat_config.command(name="set")
@click.argument("deployment_id", type=click.UUID)
@click.option(
    "--token",
    default=None,
    type=str,
    help=(
        "Token the inference runtime accepts as a Bearer credential. "
        "Omit when the deployment is open to public."
    ),
)
@click.option(
    "--default-model",
    default=None,
    type=str,
    help="Default model name sent with chat requests when --model is omitted.",
)
def set_(
    deployment_id: UUID,
    token: str | None,
    default_model: str | None,
) -> None:
    """Register or update the chat config for a deployment.

    Token registration succeeds even when the deployment has not yet
    finished provisioning. The endpoint cache is only written when the
    manager already has an ``endpoint_url`` for the deployment;
    otherwise the cache is populated lazily on the first ``chat`` call.
    """
    import sys

    if token is None and default_model is None:
        raise click.ClickException("Nothing to set: provide --token and/or --default-model.")

    connection_config = load_v2_config()
    cache = DeploymentChatCache.load()
    config = DeploymentChatConfig.load()

    async def _run() -> None:
        registry = await create_v2_registry(connection_config)
        try:
            deployment = await registry.deployment.get(deployment_id)
        finally:
            await registry.close()
        endpoint_url = deployment.network_access.endpoint_url

        if token is not None:
            config.set_token(deployment_id, token)
            config.save()

        cached_default_model: str | None = None
        if endpoint_url:
            existing_entry = cache.get(deployment_id)
            cached_default_model = default_model or (
                existing_entry.default_model if existing_entry is not None else None
            )
            cache.set(
                deployment_id,
                DeploymentChatCacheEntry(
                    endpoint_url=endpoint_url,
                    default_model=cached_default_model,
                    last_synced_at=datetime.now(UTC),
                ),
            )
            cache.save()
        elif default_model is not None:
            print(
                f"WARNING: deployment {deployment_id} has no endpoint_url yet; "
                "--default-model will be applied on the first 'chat' call after the "
                "deployment is READY.",
                file=sys.stderr,
            )

        print(f"Updated chat config for deployment {deployment_id}.")
        if cached_default_model:
            print(f"  default_model: {cached_default_model}")
        if token is not None:
            print(f"  token:         {mask_token(token)}")

    _run_async(_run)


@chat_config.command(name="show")
@click.argument("deployment_id", type=click.UUID)
def show(deployment_id: UUID) -> None:
    """Print the chat cache entry for a deployment (tokens are masked)."""
    cache = DeploymentChatCache.load()
    config = DeploymentChatConfig.load()

    entry = cache.get(deployment_id)
    token = config.get_token(deployment_id)
    if entry is None and token is None:
        raise click.ClickException(f"No chat cache entry for deployment {deployment_id}.")
    DeploymentChatFormatter.print_summary(deployment_id, entry, token)


@chat_config.command(name="clear-cache")
@click.argument("deployment_id", type=click.UUID)
def clear_cache(deployment_id: UUID) -> None:
    """Remove the cached endpoint entry for a deployment."""
    cache = DeploymentChatCache.load()
    if cache.pop(deployment_id):
        cache.save()
        print(f"Removed cache entry for deployment {deployment_id}.")
    else:
        print(f"No cache entry for deployment {deployment_id}.")


@chat_config.command(name="clear-config")
@click.argument("deployment_id", type=click.UUID)
def clear_config(deployment_id: UUID) -> None:
    """Remove the stored token for a deployment."""
    config = DeploymentChatConfig.load()
    if config.pop_token(deployment_id):
        config.save()
        print(f"Removed config entry for deployment {deployment_id}.")
    else:
        print(f"No config entry for deployment {deployment_id}.")


__all__ = ("chat", "chat_config")
