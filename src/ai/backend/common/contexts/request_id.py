import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from ai.backend.logging.structured import with_log_context

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def current_request_id() -> str | None:
    """
    Get the current request ID from the context.
    Returns None if not set.
    """
    return _request_id_var.get()


@contextmanager
def with_request_context(request_id: str | None = None) -> Iterator[None]:
    """Set the request ID and its log field to the same value, generating one if absent."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    token = _request_id_var.set(request_id)
    try:
        with with_log_context(request_id=request_id):
            yield
    finally:
        _request_id_var.reset(token)
