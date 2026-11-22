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
WATCH_RETRY_SECONDS: Final = 3


async def watch_forever(
    list_call: Callable[..., Awaitable[Any]],
    handler: Callable[[str, dict[str, Any]], None],
) -> None:
    """Call `handler(event type, object)` for each change, resuming after errors.

    `list_call` must be a wrapper (lambda) around a list API: the watch then yields plain dicts.
    """
    resource_version: str | None = None
    while True:
        try:
            w = watch.Watch()
            async with w.stream(
                list_call,
                timeout_seconds=WATCH_TIMEOUT_SECONDS,
                resource_version=resource_version,
            ) as stream:
                async for event in stream:
                    obj = event["object"]
                    if event["type"] == "ERROR":
                        resource_version = None
                        break
                    resource_version = obj["metadata"]["resourceVersion"]
                    try:
                        handler(event["type"], obj)
                    except (KeyError, TypeError) as e:
                        log.warning("watch event skipped", exc_info=e)
        except ApiException as e:
            if e.status == 410:
                resource_version = None
            else:
                log.warning("watch failed; retrying", exc_info=e)
                await asyncio.sleep(WATCH_RETRY_SECONDS)
        except (TimeoutError, OSError) as e:
            log.warning("watch connection lost; retrying", exc_info=e)
            await asyncio.sleep(WATCH_RETRY_SECONDS)
