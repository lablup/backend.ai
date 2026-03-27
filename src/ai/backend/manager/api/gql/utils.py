from __future__ import annotations

from textwrap import dedent

from aiohttp import web

from ai.backend.common.contexts.user import current_user


def dedent_strip(text: str) -> str:
    """
    Apply textwrap.dedent and strip to remove both indentation and leading/trailing whitespace.
    This is useful for GraphQL descriptions to ensure clean output in schema introspection.
    """
    return dedent(text).strip()


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
