from __future__ import annotations

import logging
import uuid
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Final

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

REQUEST_ID_HEADER: Final = "X-BackendAI-RequestID"

_request_id_var: ContextVar[str] = ContextVar("request_id")


def current_request_id() -> str | None:
    """
    Get the current request ID from the context.
    Returns None if not set.
    """
    try:
        return _request_id_var.get()
    except LookupError:
        return None


def receive_request_id(request_id: str) -> None:
    """
    Set the request ID in the current context.
    Unlike with_request_id(), this does not auto-generate a UUID if None is passed,
    and does not reset the context when done.

    Use this for fire-and-forget scenarios
    like RPC handlers where the context is scoped to the request.
    """
    _request_id_var.set(request_id)


@contextmanager
def with_request_id(request_id: str | None = None) -> Iterator[None]:
    """
    context manager to set up the request ID.
    If request_id is not provided, generates a new UUID.
    This function returns the token that can be used to reset the context later.
    """

    if request_id is None:
        request_id = str(uuid.uuid4())

    token = _request_id_var.set(request_id)
    try:
        yield
    finally:
        # Reset the context variable to its previous state
        _request_id_var.reset(token)


def bind_request_id(
    target: MutableMapping[str, Any],
    context_description: str,
    *,
    key: str = REQUEST_ID_HEADER,
) -> None:
    """
    Set the request ID if available in the current context.
    Logs a warning if no request_id is available.

    :param target: The dict to add the request ID to (e.g., headers or request body)
    :param context_description: A description of the operation for logging (e.g., "wsproxy status query")
    :param key: The key name to use (default: "X-BackendAI-RequestID")
    """
    if request_id := current_request_id():
        target[key] = request_id
    else:
        log.warning("No request_id in context for {}", context_description)
