from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from ai.backend.common.data.user.types import UserData

_user_var: ContextVar[UserData] = ContextVar("user_data")
_triggered_user_var: ContextVar[UserData] = ContextVar("triggered_user_data")


def current_user() -> UserData | None:
    """
    Get the effective (acting) user from the context.

    This is the permission/scope subject that every operation keys off — NOT
    necessarily the caller. In a normal request it equals the authenticated
    caller; while a super admin impersonates a target it holds the target user.
    Use ``triggered_user()`` to get the caller. Returns None if not set.
    """
    try:
        return _user_var.get()
    except LookupError:
        return None


@contextmanager
def with_user(user: UserData) -> Iterator[None]:
    """
    Context manager to set up the effective (acting) user data.
    This is useful for setting the user data in the context for the duration of a block of code.
    This function returns the token that can be used to reset the context later.
    """
    token = _user_var.set(user)
    try:
        yield
    finally:
        # Reset the context variable to its previous state
        _user_var.reset(token)


def triggered_user() -> UserData | None:
    """
    Get the trigger (requesting) user from the context.

    This is the authenticated caller who triggered the request. In a normal
    request it equals ``current_user()``; while a super admin impersonates a
    target it holds the super admin. Returns None if not set.
    """
    try:
        return _triggered_user_var.get()
    except LookupError:
        return None


@contextmanager
def with_triggered_user(user: UserData) -> Iterator[None]:
    """
    Context manager to set up the trigger (requesting) user data.
    Mirrors ``with_user`` but for the caller identity rather than the effective subject.
    """
    token = _triggered_user_var.set(user)
    try:
        yield
    finally:
        _triggered_user_var.reset(token)


def is_impersonating() -> bool:
    """
    Return True while a super admin is impersonating another user, i.e. the trigger
    (requesting) user and the effective (acting) user are both set and differ.
    """
    trigger = triggered_user()
    acting = current_user()
    return trigger is not None and acting is not None and trigger.user_id != acting.user_id
