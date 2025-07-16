from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

_user_id_var: ContextVar[str] = ContextVar("user_id")


def current_user_id() -> Optional[str]:
    """
    Get the current user ID from the context.
    Returns None if not set.
    """
    try:
        return _user_id_var.get()
    except LookupError:
        return None


@contextmanager
def with_user_id(user_id: str) -> Iterator[None]:
    """
    context manager to set up the user ID.
    This is useful for setting the user ID in the context for the duration of a block of code.
    This function returns the token that can be used to reset the context later.
    """
    token = _user_id_var.set(user_id)
    try:
        yield
    finally:
        # Reset the context variable to its previous state
        _user_id_var.reset(token)
