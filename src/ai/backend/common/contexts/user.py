from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from ai.backend.common.data.user.types import UserData
from ai.backend.logging.structured import LogValue, with_log_context

_user_var: ContextVar[UserData | None] = ContextVar("user_data", default=None)
_triggered_user_var: ContextVar[UserData | None] = ContextVar("triggered_user_data", default=None)


def current_user() -> UserData | None:
    """
    Get the effective (acting) user from the context.

    This is the permission/scope subject that every operation keys off — NOT
    necessarily the caller. In a normal request it equals the authenticated
    caller; while a super admin impersonates a target it holds the target user.
    Use ``triggered_user()`` to get the caller. Returns None if not set.
    """
    return _user_var.get()


def triggered_user() -> UserData | None:
    """
    Get the trigger (requesting) user from the context.

    This is the authenticated caller who triggered the request. In a normal
    request it equals ``current_user()``; while a super admin impersonates a
    target it holds the super admin. Returns None if not set.
    """
    return _triggered_user_var.get()


@contextmanager
def with_user_context(
    user: UserData | None,
    triggered_user: UserData | None = None,
) -> Iterator[None]:
    """Set the effective and trigger users and their log fields to the same values.

    `triggered_user_id` is logged only when the trigger user differs from the effective user.
    """
    log_fields: dict[str, LogValue] = {}
    if user is not None:
        log_fields["user_id"] = user.user_id
    if triggered_user is not None and (user is None or triggered_user.user_id != user.user_id):
        log_fields["triggered_user_id"] = triggered_user.user_id
    user_token = _user_var.set(user) if user is not None else None
    triggered_token = (
        _triggered_user_var.set(triggered_user) if triggered_user is not None else None
    )
    try:
        with with_log_context(**log_fields):
            yield
    finally:
        if triggered_token is not None:
            _triggered_user_var.reset(triggered_token)
        if user_token is not None:
            _user_var.reset(user_token)
