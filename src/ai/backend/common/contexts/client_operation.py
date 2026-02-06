from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_client_operation_var: ContextVar[str] = ContextVar("client_operation")


def get_client_operation() -> str:
    """
    Get the current client operation from the context.
    Returns empty string if not set.
    """
    try:
        return _client_operation_var.get()
    except LookupError:
        return ""


@contextmanager
def with_client_operation(client_operation: str) -> Iterator[None]:
    """
    Context manager to set up the client operation.
    """
    token = _client_operation_var.set(client_operation)
    try:
        yield
    finally:
        _client_operation_var.reset(token)
