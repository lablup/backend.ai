from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_client_operation_var: ContextVar[str] = ContextVar("client_operation", default="")


def get_client_operation() -> str:
    return _client_operation_var.get()


@contextmanager
def with_client_operation(operation: str) -> Iterator[None]:
    token = _client_operation_var.set(operation)
    try:
        yield
    finally:
        _client_operation_var.reset(token)
