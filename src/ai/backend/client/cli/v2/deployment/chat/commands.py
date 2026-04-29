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
from ai.backend.client.cli.v2.deployment.chat.storage import (
    load_chat_cache,
    load_chat_config,
    save_chat_cache,
    save_chat_config,
)
from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config
from ai.backend.common.data.deployment_chat import DeploymentChatCacheEntry
from ai.backend.common.dto.clients.openai_compat import ChatCompletionRequest


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
    help=(
        "Model name to send. Resolution order: this flag, then the user-set "
        "config.json model, then the auto-cached cache.json default_model, "
        "then GET /v1/models on the deployment."
    ),
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

    cache = load_chat_cache()
    chat_config = load_chat_config()

    if not isinstance(params, dict):
        raise click.ClickException("--params must be a JSON object.")
    extra_body: dict[str, Any] = params

    async def _run() -> None:
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
            save_chat_cache(cache)

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
                # Resolution: --model > config.model (user-set) >
                # cache.default_model (auto) > GET /v1/models (auto, cached).
                request_model = (
                    model or chat_config.get_model(deployment_id) or endpoint_entry.default_model
                )
                if request_model is None:
                    # No explicit --model, no user-set config, no cached
                    # default — ask the OpenAI-compat endpoint itself which
                    # models it serves and adopt the first one as the
                    # cached default (matches webui ChatCard.tsx behaviour).
                    models_response = await client.list_models(endpoint_entry.endpoint_url, token)
                    if not models_response.data:
                        raise click.ClickException(
                            f"Deployment {deployment_id} did not advertise any models "
                            f"on /v1/models. Set one explicitly with:\n"
                            f"  ./bai deployment chat-config set {deployment_id} "
                            f"--model <name>"
                        )
                    request_model = models_response.data[0].id
                    endpoint_entry = DeploymentChatCacheEntry(
                        endpoint_url=endpoint_entry.endpoint_url,
                        default_model=request_model,
                        last_synced_at=endpoint_entry.last_synced_at,
                    )
                    cache.set(deployment_id, endpoint_entry)
                    save_chat_cache(cache)

                request = ChatCompletionRequest.model_validate({
                    **extra_body,
                    "model": request_model,
                    "messages": [{"role": "user", "content": content}],
                })
                body = request.model_dump(mode="json")
                response = await client.chat_completion(endpoint_entry.endpoint_url, token, body)
            except DeploymentAuthError as e:
                # 401/403 from /v1/models or /v1/chat/completions: invalidate
                # the cached token so the next ``chat`` call surfaces the same
                # hint instead of silently re-sending a stale key. Other
                # BackendAPIErrors fall through to ``_run_async`` which formats
                # the manager-style status/title/msg payload generically.
                if token is not None and chat_config.pop_token(deployment_id):
                    save_chat_config(chat_config)
                raise click.ClickException(
                    f"The inference endpoint rejected the configured token for "
                    f"deployment {deployment_id}. The stored token has been cleared; "
                    f"re-register with:\n"
                    f"  ./bai deployment chat-config set {deployment_id} --token <token>"
                ) from e
        print(json.dumps(response, indent=2, ensure_ascii=False, default=str))

    _run_async(_run)


# ---------------------------------------------------------------------------
# chat-config
# ---------------------------------------------------------------------------


@click.group(name="chat-config")
def chat_config() -> None:
    """Manage user-supplied chat config (Bearer token, chosen model) per
    deployment.

    The deployment's ``endpoint_url`` and the auto-derived
    ``default_model`` from ``GET /v1/models`` live in the cache file and
    are managed by ``./bai deployment chat`` itself; this group only
    edits the user-managed config file (``~/.backend.ai/deployment_chat/
    config.json``).
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
    "--model",
    default=None,
    type=str,
    help=(
        "Model name to use for ``chat`` calls on this deployment. "
        "Takes precedence over the auto-derived default_model in cache.json."
    ),
)
def set_(
    deployment_id: UUID,
    token: str | None,
    model: str | None,
) -> None:
    """Register or update the chat config for a deployment.

    Writes only to ``config.json`` — the manager is not contacted, so this
    works regardless of deployment provisioning state and stays usable
    offline.
    """
    if token is None and model is None:
        raise click.ClickException("Nothing to set: provide --token and/or --model.")

    config = load_chat_config()
    if token is not None:
        config.set_token(deployment_id, token)
    if model is not None:
        config.set_model(deployment_id, model)
    save_chat_config(config)

    print(f"Updated chat config for deployment {deployment_id}.")
    if model is not None:
        print(f"  model: {model}")
    if token is not None:
        print(f"  token: {mask_token(token)}")


@chat_config.command(name="show")
@click.argument("deployment_id", type=click.UUID)
def show(deployment_id: UUID) -> None:
    """Print the chat cache + config entry for a deployment (tokens are masked)."""
    cache = load_chat_cache()
    config = load_chat_config()

    entry = cache.get(deployment_id)
    config_entry = config.get(deployment_id)
    if entry is None and config_entry is None:
        raise click.ClickException(f"No chat state for deployment {deployment_id}.")
    DeploymentChatFormatter.print_summary(
        deployment_id,
        entry,
        config_entry.token if config_entry is not None else None,
        config_entry.model if config_entry is not None else None,
    )


@chat_config.command(name="clear")
@click.argument("deployment_id", type=click.UUID)
def clear(deployment_id: UUID) -> None:
    """Remove the user-managed config entry (token + model) for a deployment.

    The auto-managed cache entry (``endpoint_url``, ``default_model``,
    ``last_synced_at``) is left alone — it expires on its own 24-hour TTL
    and gets refreshed by the next ``chat`` call. Use ``clear-cache`` to
    drop it immediately.
    """
    config = load_chat_config()
    if config.pop(deployment_id):
        save_chat_config(config)
        print(f"Removed config entry for deployment {deployment_id}.")
    else:
        print(f"No config entry for deployment {deployment_id}.")


@chat_config.command(name="clear-cache")
@click.argument("deployment_id", type=click.UUID)
def clear_cache(deployment_id: UUID) -> None:
    """Remove the auto-managed cache entry for a deployment.

    Forces the next ``chat`` call to re-fetch ``endpoint_url`` from the
    manager and re-derive ``default_model`` from ``GET /v1/models``. The
    user-managed config entry (token + model) is left alone.
    """
    cache = load_chat_cache()
    if cache.pop(deployment_id):
        save_chat_cache(cache)
        print(f"Removed cache entry for deployment {deployment_id}.")
    else:
        print(f"No cache entry for deployment {deployment_id}.")


__all__ = ("chat", "chat_config")
