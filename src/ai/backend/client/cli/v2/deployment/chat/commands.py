"""User-facing CLI: ``./bai deployment chat`` and ``chat-config``."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import click
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ai.backend.cli.params import JSONParamType
from ai.backend.client.cli.v2.deployment.chat.types import (
    DeploymentChatCacheEntry,
    IncompatibleChatCacheError,
    IncompatibleChatConfigError,
)
from ai.backend.client.cli.v2.deployment.chat.utils import (
    load_chat_cache,
    load_chat_config,
    mask_token,
    save_chat_cache,
    save_chat_config,
)
from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config


class _ServedModelEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str


class _ServedModelsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: list[_ServedModelEntry] = Field(default_factory=list)


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

    Sampling parameters (temperature, top_p, max_tokens, etc.) are not
    exposed as individual flags because their schema differs across
    runtime variants. Pass them through ``--params`` instead.
    """
    import json

    from ai.backend.client.v2.deployment_chat import (
        DeploymentChatAuthError,
        DeploymentChatClient,
    )

    connection = load_v2_config()

    try:
        cache = load_chat_cache()
        chat_config_store = load_chat_config()
    except (IncompatibleChatCacheError, IncompatibleChatConfigError) as e:
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
        api_key = chat_config_store.get_token(deployment_id)
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
    default_model: str | None,
) -> None:
    """Register or update the chat cache entry for a deployment."""
    connection = load_v2_config()
    try:
        cache = load_chat_cache()
        chat_config_store = load_chat_config()
    except (IncompatibleChatCacheError, IncompatibleChatConfigError) as e:
        raise click.ClickException(str(e)) from e

    existing_entry = cache.get(deployment_id)
    resolved_key = api_key if api_key is not None else chat_config_store.get_token(deployment_id)

    async def _run() -> None:
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

        if default_model is not None:
            served_model: str | None = default_model
        else:
            served_model = await _discover_model(
                endpoint_url,
                resolved_key,
                connection.skip_ssl_verification,
                existing_entry.default_model if existing_entry is not None else None,
            )

        cache.upsert(
            deployment_id,
            DeploymentChatCacheEntry(
                endpoint_url=endpoint_url,
                default_model=served_model,
                last_synced_at=datetime.now(UTC),
            ),
        )
        save_chat_cache(cache)
        if resolved_key is not None:
            chat_config_store.set_token(deployment_id, resolved_key)
            save_chat_config(chat_config_store)

        print(f"Updated chat cache entry for deployment {deployment_id}.")
        if served_model:
            print(f"  default_model: {served_model}")
        print(f"  api_key:       {mask_token(resolved_key)}")

    _run_async(_run)


async def _discover_model(
    endpoint_url: str,
    api_key: str | None,
    skip_ssl_verification: bool,
    fallback: str | None,
) -> str | None:
    """Call ``GET {endpoint}/v1/models`` to learn the served model name."""
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
    try:
        parsed = _ServedModelsResponse.model_validate(payload)
    except ValidationError:
        return fallback
    return parsed.data[0].id if parsed.data else fallback


@chat_config.command(name="show")
@click.argument("deployment_id", type=click.UUID, required=False)
def show(deployment_id: UUID | None) -> None:
    """Print one or all chat cache entries (API keys are masked)."""
    try:
        cache = load_chat_cache()
        chat_config_store = load_chat_config()
    except (IncompatibleChatCacheError, IncompatibleChatConfigError) as e:
        raise click.ClickException(str(e)) from e

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
    try:
        cache = load_chat_cache()
        chat_config_store = load_chat_config()
    except (IncompatibleChatCacheError, IncompatibleChatConfigError) as e:
        raise click.ClickException(str(e)) from e

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
