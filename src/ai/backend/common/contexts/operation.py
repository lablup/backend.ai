from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_client_operation_var: ContextVar[str] = ContextVar("client_operation", default="")


def get_client_operation() -> str:
    """
    Return the current client operation name from the context.
    Returns an empty string if no operation context has been established,
    unlike other context getters that return None for unset values.
    """
    return _client_operation_var.get()


@contextmanager
def with_client_operation(operation: str) -> Iterator[None]:
    """
    Context manager to set the client operation name for the current scope.
    Resets the context variable to its previous state on exit.
    """
    token = _client_operation_var.set(operation)
    try:
        yield
    finally:
        _client_operation_var.reset(token)
