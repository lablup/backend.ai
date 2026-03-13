from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_client_ip_var: ContextVar[str] = ContextVar("client_ip")


def current_client_ip() -> str | None:
    """
    Get the current client IP from the context.
    Returns None if not set.
    """
    try:
        return _client_ip_var.get()
    except LookupError:
        return None


@contextmanager
def with_client_ip(ip: str) -> Iterator[None]:
    """
    Context manager to set the client IP in the context.
    """
    token = _client_ip_var.set(ip)
    try:
        yield
    finally:
        _client_ip_var.reset(token)
