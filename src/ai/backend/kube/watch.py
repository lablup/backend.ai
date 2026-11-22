from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Final

from kubernetes_asyncio import watch
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

WATCH_TIMEOUT_SECONDS: Final = 300
LIST_TIMEOUT_SECONDS: Final = 60
WATCH_RETRY_SECONDS: Final = 1.0
WATCH_RETRY_MAX_SECONDS: Final = 30.0


async def list_objects(
    list_call: Callable[..., Awaitable[Any]],
) -> tuple[list[dict[str, Any]], str]:
    """Every object of a list API as plain dicts, and the list's resourceVersion."""
    resp = await list_call(_preload_content=False, _request_timeout=LIST_TIMEOUT_SECONDS)
    try:
        if not 200 <= resp.status <= 299:
            raise ApiException(status=resp.status, reason=await resp.text())
        body = await resp.json()
    finally:
        resp.release()
    return list(body.get("items") or []), str(body["metadata"]["resourceVersion"])


async def watch_forever(
    list_call: Callable[..., Awaitable[Any]],
    handler: Callable[[str, dict[str, Any]], None],
    *,
    on_relist: Callable[[list[dict[str, Any]]], None] | None = None,
) -> None:
    """Call `handler(event type, object)` for each change, resuming after errors.

    `list_call` must be a wrapper (lambda) around a list API: the watch then yields plain dicts.
    Each fresh start lists first: `on_relist(items)` gets every current object, `handler` gets
    each as ADDED, then events stream from the list's resourceVersion. Only cancellation ends it.
    """
    resource_version: str | None = None
    backoff = WATCH_RETRY_SECONDS
    while True:
        try:
            if resource_version is None:
                items, resource_version = await list_objects(list_call)
                if on_relist is not None:
                    _call(on_relist, items)
                for item in items:
                    _call(handler, "ADDED", item)
            w = watch.Watch()
            async with w.stream(
                list_call,
                timeout_seconds=WATCH_TIMEOUT_SECONDS,
                resource_version=resource_version,
                allow_watch_bookmarks=True,
            ) as stream:
                async for event in stream:
                    if event["type"] == "ERROR":
                        resource_version = None
                        break
                    obj = event["raw_object"] if "raw_object" in event else event["object"]
                    resource_version = obj["metadata"]["resourceVersion"]
                    if event["type"] != "BOOKMARK":
                        _call(handler, event["type"], obj)
            backoff = WATCH_RETRY_SECONDS
        except ApiException as e:
            if e.status == 410:  # the resourceVersion is too old: list again
                resource_version = None
                continue
            log.warning("watch failed; retrying", status=e.status, exc_info=e)
            backoff = await _sleep(backoff)
        except Exception as e:
            log.warning("watch connection lost; retrying", exc_info=e)
            backoff = await _sleep(backoff)


def _call(func: Callable[..., None], *args: Any) -> None:
    try:
        func(*args)
    except Exception:
        log.exception("watch handler failed")


async def _sleep(backoff: float) -> float:
    await asyncio.sleep(backoff)
    return min(backoff * 2, WATCH_RETRY_MAX_SECONDS)
