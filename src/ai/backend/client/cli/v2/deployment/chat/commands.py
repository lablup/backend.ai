"""User-facing CLI: ``./bai deployment chat`` and ``chat-config``."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import click

from ai.backend.cli.params import JSONParamType
from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCache,
    DeploymentChatCacheEntry,
)
from ai.backend.client.cli.v2.deployment.chat.utils import (
    load_chat_cache,
    load_chat_config,
    mask_token,
    save_chat_cache,
    save_chat_config,
)
from ai.backend.client.cli.v2.helpers import V2ConnectionConfig, create_v2_registry, load_v2_config


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


async def _resolve_endpoint_entry(
    cache: DeploymentChatCache,
    deployment_id: UUID,
    connection: V2ConnectionConfig,
    *,
    default_model_override: str | None = None,
) -> DeploymentChatCacheEntry:
    """Return the deployment's cached endpoint entry, fetching from the manager on miss.

    This is the only place that writes to the chat cache. ``set_`` and the
    ``chat`` command both delegate here so the cache file is touched at
    most once per command invocation.

    When ``default_model_override`` is given, the cached entry is rewritten
    with the new model regardless of an existing entry.
    """
    existing = cache.get(deployment_id)
    if existing is not None and default_model_override is None:
        return existing

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

    served_model: str | None
    if default_model_override is not None:
        served_model = default_model_override
    else:
        served_model = existing.default_model if existing is not None else None

    new_entry = DeploymentChatCacheEntry(
        endpoint_url=endpoint_url,
        default_model=served_model,
        last_synced_at=datetime.now(UTC),
    )
    cache.upsert(deployment_id, new_entry)
    save_chat_cache(cache)
    return new_entry


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

    Sampling parameters (temperature, top_p, max_tokens, etc.) are not
    exposed as individual flags because their schema differs across
    runtime variants. Pass them through ``--params`` instead.
    """
    import json

    from ai.backend.client.v2.deployment_chat import (
        DeploymentChatAuthError,
        DeploymentChatClient,
        DeploymentChatClientArgs,
    )

    connection = load_v2_config()

    cache = load_chat_cache()
    chat_config_store = load_chat_config()

    if not isinstance(params, dict):
        raise click.ClickException("--params must be a JSON object.")
    extra_body: dict[str, Any] = params

    async def _run() -> None:
        from ai.backend.client.exceptions import BackendAPIError

        endpoint_entry = await _resolve_endpoint_entry(cache, deployment_id, connection)
        request_model = model or endpoint_entry.default_model
        if request_model is None:
            raise click.ClickException(
                f"No --model given and no default_model cached for deployment {deployment_id}.\n"
                "Set one with:\n"
                f"  ./bai deployment chat-config set {deployment_id} --default-model <name>"
            )

        body: dict[str, Any] = {
            **extra_body,
            "model": request_model,
            "messages": [{"role": "user", "content": content}],
        }
        api_key = chat_config_store.get_token(deployment_id)
        client_args = DeploymentChatClientArgs(
            skip_ssl_verification=connection.skip_ssl_verification,
        )
        async with DeploymentChatClient(client_args) as client:
            try:
                response = await client.chat_completion(
                    endpoint_entry.endpoint_url,
                    api_key,
                    body,
                )
            except DeploymentChatAuthError as e:
                raise click.ClickException(
                    f"The inference endpoint rejected the configured API key for "
                    f"deployment {deployment_id}. Re-register with:\n"
                    f"  ./bai deployment chat-config set {deployment_id} --token <api_key>"
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
    """Manage stored API keys and default model names for deployment chat.

    The deployment's ``endpoint_url`` is auto-managed; ``--token`` and
    ``--default-model`` are user-supplied.
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
    "--default-model",
    default=None,
    type=str,
    help="Default model name sent with chat requests when --model is omitted.",
)
def set_(
    deployment_id: UUID,
    api_key: str | None,
    default_model: str | None,
) -> None:
    """Register or update the chat config for a deployment."""
    if api_key is None and default_model is None:
        raise click.ClickException("Nothing to set: provide --token and/or --default-model.")

    connection = load_v2_config()
    cache = load_chat_cache()
    chat_config_store = load_chat_config()

    resolved_key = api_key if api_key is not None else chat_config_store.get_token(deployment_id)

    async def _run() -> None:
        endpoint_entry = await _resolve_endpoint_entry(
            cache,
            deployment_id,
            connection,
            default_model_override=default_model,
        )
        if api_key is not None:
            chat_config_store.set_token(deployment_id, api_key)
            save_chat_config(chat_config_store)

        print(f"Updated chat config for deployment {deployment_id}.")
        if endpoint_entry.default_model:
            print(f"  default_model: {endpoint_entry.default_model}")
        print(f"  api_key:       {mask_token(resolved_key)}")

    _run_async(_run)


@chat_config.command(name="show")
@click.argument("deployment_id", type=click.UUID, required=False)
def show(deployment_id: UUID | None) -> None:
    """Print one or all chat cache entries (API keys are masked)."""
    cache = load_chat_cache()
    chat_config_store = load_chat_config()

    if deployment_id is not None:
        entry = cache.get(deployment_id)
        token = chat_config_store.get_token(deployment_id)
        if entry is None and token is None:
            raise click.ClickException(f"No chat cache entry for deployment {deployment_id}.")
        _print_entry(deployment_id, entry, token)
        return

    dep_ids = set(cache.deployments) | set(chat_config_store.tokens)
    if not dep_ids:
        print("No chat cache entries.")
        return
    for dep_id in dep_ids:
        _print_entry(dep_id, cache.get(dep_id), chat_config_store.get_token(dep_id))
        print()


@chat_config.command(name="clear")
@click.argument("deployment_id", type=click.UUID)
def clear(deployment_id: UUID) -> None:
    """Remove the chat cache entry and stored token for a deployment."""
    cache = load_chat_cache()
    chat_config_store = load_chat_config()

    removed_entry = cache.remove(deployment_id)
    removed_token = chat_config_store.clear_token(deployment_id)
    if removed_entry:
        save_chat_cache(cache)
    if removed_token:
        save_chat_config(chat_config_store)
    if removed_entry or removed_token:
        print(f"Removed chat cache entry for deployment {deployment_id}.")
    else:
        print(f"No chat cache entry for deployment {deployment_id}.")


def _print_entry(
    deployment_id: UUID,
    entry: DeploymentChatCacheEntry | None,
    token: str | None,
) -> None:
    print(f"deployment_id : {deployment_id}")
    if entry is not None:
        for line in entry.format_summary():
            print(line)
    else:
        print("endpoint_url  : -")
        print("default_model : -")
        print("last_synced_at: -")
    print(f"api_key       : {mask_token(token)}")


__all__ = ("chat", "chat_config")
