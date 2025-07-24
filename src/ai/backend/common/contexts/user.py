from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

from ai.backend.common.data.user.types import UserData

_user_var: ContextVar[UserData] = ContextVar("user_data")


def current_user() -> Optional[UserData]:
    """
    Get the current user ID from the context.
    Returns None if not set.
    """
    try:
        return _user_var.get()
    except LookupError:
        return None


@contextmanager
def with_user(user: UserData) -> Iterator[None]:
    """
    Context manager to set up the user data.
    This is useful for setting the user data in the context for the duration of a block of code.
    This function returns the token that can be used to reset the context later.
    """
    token = _user_var.set(user)
    try:
        yield
    finally:
        # Reset the context variable to its previous state
        _user_var.reset(token)
