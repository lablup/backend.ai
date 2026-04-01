from __future__ import annotations

from aiohttp import web

from ai.backend.common.contexts.user import current_user
from ai.backend.common.utils import dedent_strip

__all__ = (
    "check_admin_only",
    "dedent_strip",
)


def check_admin_only() -> None:
    """
    Verify that the current user is a superadmin.

    This check is required for all admin_* prefixed APIs as defined in BEP-1041.

    Raises:
        web.HTTPForbidden: If the current user is not a superadmin.
    """
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Admin exclusive access")
