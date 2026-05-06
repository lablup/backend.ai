"""User-facing CLI: ``./bai deployment chat``, ``chat-config``, ``chat-cache``, ``chat-history``."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

import click

from ai.backend.cli.params import JSONParamType
from ai.backend.client.cli.v2.deployment.chat.formatter import (
    DeploymentChatFormatter,
    mask_token,
)
from ai.backend.client.cli.v2.deployment.chat.types import (
    DEFAULT_CHAT_HISTORY_LIMIT,
    DeploymentChatCache,
    DeploymentChatCacheEntry,
    DeploymentChatConfig,
    DeploymentChatHistory,
)
from ai.backend.client.cli.v2.helpers import (
    create_appproxy_registry,
    create_v2_registry,
    load_v2_config,
)
from ai.backend.common.dto.clients.openai_compat import ChatCompletionRequest
from ai.backend.common.identifier.deployment import DeploymentID


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
@click.argument("message", type=str)
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
        "The 'model' and 'messages' fields are always overridden by --model and MESSAGE."
    ),
)
@click.option(
    "--history-limit",
    default=DEFAULT_CHAT_HISTORY_LIMIT,
    type=click.IntRange(min=0),
    show_default=True,
    help=(
        "Maximum number of past messages from this deployment's persisted "
        "history to replay as context. Set to 0 to skip context for this "
        "turn (the round is still recorded; use `chat-history clear` to "
        "wipe the persisted transcript)."
    ),
)
def chat(
    deployment_id: DeploymentID,
    message: str,
    model: str | None,
    params: Any,
    history_limit: int,
) -> None:
    """Send a one-shot chat completion request to a deployed model.

    Targets OpenAI-compatible Chat Completions endpoints
    (vLLM / SGLang / NIM / TGI in messages-api mode / custom containers
    that follow the same contract). Sampling parameters such as
    temperature and top_p differ between runtime variants — pass them
    through ``--params``.
    """
    from ai.backend.client.v2.exceptions import DeploymentAuthError

    connection_config = load_v2_config()

    cache = DeploymentChatCache.load()
    chat_config = DeploymentChatConfig.load()
    history = DeploymentChatHistory.load()

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
            cache.save()

        token = chat_config.get_token(deployment_id)
        appproxy_registry = await create_appproxy_registry(connection_config)
        try:
            client = appproxy_registry.deployment_chat
            # Resolution: --model > config.model (user-set) >
            # cache.default_model (auto) > GET /v1/models (auto, cached).
            request_model = (
                model or chat_config.get_model(deployment_id) or endpoint_entry.default_model
            )
            try:
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
                    cache.save()

                past_messages = history.slice(deployment_id, history_limit)
                request_messages: list[dict[str, str]] = [
                    *({"role": past.role, "content": past.content} for past in past_messages),
                    {"role": "user", "content": message},
                ]
                request = ChatCompletionRequest.model_validate({
                    **extra_body,
                    "model": request_model,
                    "messages": request_messages,
                })
                body = request.model_dump(mode="json")
                response = await client.chat_completion(endpoint_entry.endpoint_url, token, body)
            except DeploymentAuthError as e:
                # 401/403 from /v1/models or /v1/chat/completions: invalidate
                # the cached token so the next ``chat`` call surfaces the same
                # hint instead of silently re-sending a stale key. Other
                # BackendAPIErrors fall through to ``_run_async`` which formats
                # the manager-style status/title/msg payload generically.
                if token is not None and chat_config.clear_token(deployment_id):
                    chat_config.save()
                raise click.ClickException(
                    f"The inference endpoint rejected the configured token for "
                    f"deployment {deployment_id}. The stored token has been cleared; "
                    f"re-register with:\n"
                    f"  ./bai deployment chat-config set {deployment_id} --token <token>"
                ) from e
        finally:
            await appproxy_registry.close()
        # Only persist when both sides of the round are present, so the file
        # never carries half-conversations that would skew future context.
        assistant_message = response.assistant_message
        if assistant_message is not None:
            now = datetime.now(UTC)
            history.append(deployment_id, "user", message, created_at=now)
            history.append(deployment_id, "assistant", assistant_message, created_at=now)
            history.save()
        print(response.model_dump_json(indent=2))

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
    deployment_id: DeploymentID,
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

    config = DeploymentChatConfig.load()
    if token is not None:
        config.set_token(deployment_id, token)
    if model is not None:
        config.set_model(deployment_id, model)
    config.save()

    print(f"Updated chat config for deployment {deployment_id}.")
    if model is not None:
        print(f"  model: {model}")
    if token is not None:
        print(f"  token: {mask_token(token)}")


@chat_config.command(name="show")
@click.argument("deployment_id", type=click.UUID)
def show(deployment_id: DeploymentID) -> None:
    """Print the user-managed chat config entry for a deployment (tokens are masked).

    Only the user-managed fields (``token``, ``model``) are shown; the
    auto-managed cache (``endpoint_url``, ``default_model``,
    ``last_synced_at``) is treated as internal CLI state and not part of
    this view.
    """
    config_entry = DeploymentChatConfig.load().get(deployment_id)
    if config_entry is None:
        raise click.ClickException(f"No chat config for deployment {deployment_id}.")
    DeploymentChatFormatter.print_config(deployment_id, config_entry)


@chat_config.command(name="clear")
@click.argument("deployment_id", type=click.UUID)
def clear(deployment_id: DeploymentID) -> None:
    """Remove the user-managed config entry (token + model) for a deployment.

    The auto-managed cache entry (``endpoint_url``, ``default_model``,
    ``last_synced_at``) is left alone — it expires on its own 24-hour TTL
    and gets refreshed by the next ``chat`` call. Use
    ``./bai deployment chat-cache clear`` to drop it immediately.
    """
    config = DeploymentChatConfig.load()
    if config.delete(deployment_id):
        config.save()
        print(f"Removed config entry for deployment {deployment_id}.")
    else:
        print(f"No config entry for deployment {deployment_id}.")


# ---------------------------------------------------------------------------
# chat-cache
# ---------------------------------------------------------------------------


@click.group(name="chat-cache")
def chat_cache() -> None:
    """Inspect or drop the auto-managed chat cache entry per deployment.

    The cache stores values the CLI derived itself — the deployment's
    ``endpoint_url`` (resolved from the manager) and the inferred
    ``default_model`` (from ``GET /v1/models``) — under
    ``~/.backend.ai/deployment_chat/cache.json`` with a 24-hour TTL.
    User-supplied state (``token``, ``model``) lives in ``chat-config``
    and is not touched by this group.
    """


@chat_cache.command(name="show")
@click.argument("deployment_id", type=click.UUID)
def cache_show(deployment_id: DeploymentID) -> None:
    """Print the auto-managed chat cache entry for a deployment."""
    entry = DeploymentChatCache.load().get(deployment_id)
    if entry is None:
        raise click.ClickException(f"No chat cache for deployment {deployment_id}.")
    DeploymentChatFormatter.print_cache(deployment_id, entry)


@chat_cache.command(name="clear")
@click.argument("deployment_id", type=click.UUID)
def cache_clear(deployment_id: DeploymentID) -> None:
    """Remove the auto-managed cache entry for a deployment.

    Forces the next ``chat`` call to re-fetch ``endpoint_url`` from the
    manager and re-derive ``default_model`` from ``GET /v1/models``. The
    user-managed config entry (token + model) is left alone.
    """
    cache = DeploymentChatCache.load()
    if cache.delete(deployment_id):
        cache.save()
        print(f"Removed cache entry for deployment {deployment_id}.")
    else:
        print(f"No cache entry for deployment {deployment_id}.")


# ---------------------------------------------------------------------------
# chat-history
# ---------------------------------------------------------------------------


@click.group(name="chat-history")
def chat_history() -> None:
    """Manage per-deployment chat transcripts.

    The ``chat`` command auto-records each user/assistant round into
    ``~/.backend.ai/deployment_chat/history.json`` so subsequent calls
    can replay recent turns as context. Use this group to inspect or
    wipe what has been persisted.
    """


@chat_history.command(name="show")
@click.argument("deployment_id", type=click.UUID)
@click.option(
    "--limit",
    default=None,
    type=click.IntRange(min=1),
    help="Print only the most recent N messages (default: all persisted).",
)
def history_show(deployment_id: DeploymentID, limit: int | None) -> None:
    """Print the persisted transcript for a deployment."""
    history = DeploymentChatHistory.load()
    messages = history.get(deployment_id)
    if messages is None:
        print(f"No chat history for deployment {deployment_id}.")
        return
    if not messages:
        print(f"Chat history for deployment {deployment_id} is empty.")
        return
    visible = messages if limit is None else messages[-limit:]
    print(f"deployment_id : {deployment_id}")
    print(f"messages      : {len(messages)} persisted (showing {len(visible)})")
    for message in visible:
        print(f"  [{message.created_at.isoformat()}] {message.role}: {message.content}")


@chat_history.command(name="clear")
@click.argument("deployment_id", type=click.UUID)
def history_clear(deployment_id: DeploymentID) -> None:
    """Drop the persisted transcript for a deployment.

    The next ``chat`` call starts a fresh context. Cache and config
    entries are unaffected.
    """
    history = DeploymentChatHistory.load()
    if history.clear(deployment_id):
        history.save()
        print(f"Cleared chat history for deployment {deployment_id}.")
    else:
        print(f"No chat history for deployment {deployment_id}.")


__all__ = ("chat", "chat_cache", "chat_config", "chat_history")
