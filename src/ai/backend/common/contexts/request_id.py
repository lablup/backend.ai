import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

_request_id_var: ContextVar[str] = ContextVar("request_id")


def current_request_id() -> Optional[str]:
    """
    Get the current request ID from the context.
    Returns None if not set.
    """
    try:
        return _request_id_var.get()
    except LookupError:
        return None


@contextmanager
def with_request_id(request_id: Optional[str] = None) -> Iterator[None]:
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
