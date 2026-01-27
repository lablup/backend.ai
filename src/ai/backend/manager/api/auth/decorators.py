"""
Auth decorators for authorization enforcement.

This module provides decorators that mark handler requirements for the auth middleware.
The actual authorization check is performed by the auth middleware.

- @auth_required: Requires authenticated user
- @auth_required_for_method: Requires authenticated user (for class methods)
- @admin_required: Requires admin privileges
- @admin_required_for_method: Requires admin privileges (for class methods)
- @superadmin_required: Requires superadmin privileges
- @superadmin_required_for_method: Requires superadmin privileges (for class methods)

TODO: Migrate authorization logic fully into middleware layer.
"""

from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.manager.api.utils import set_handler_attr
from ai.backend.manager.errors.auth import AuthorizationFailed

__all__ = (
    "auth_required",
    "auth_required_for_method",
    "admin_required",
    "admin_required_for_method",
    "superadmin_required",
    "superadmin_required_for_method",
)


def auth_required(handler: Handler) -> Handler:
    @functools.wraps(handler)
    async def wrapped(request: web.Request) -> web.StreamResponse:
        if request.get("is_authorized", False):
            return await handler(request)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "user")
    return wrapped


def auth_required_for_method(
    method: Callable[..., Awaitable[web.StreamResponse]],
) -> Callable[..., Awaitable[web.StreamResponse]]:
    @functools.wraps(method)
    async def wrapped(
        self: Any, request: web.Request, *args: Any, **kwargs: Any
    ) -> web.StreamResponse:
        if request.get("is_authorized", False):
            return await method(self, request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "user")
    return wrapped


def admin_required(handler: Handler) -> Handler:
    @functools.wraps(handler)
    async def wrapped(request: web.Request, *args: Any, **kwargs: Any) -> web.StreamResponse:
        if request.get("is_authorized", False) and request.get("is_admin", False):
            return await handler(request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "admin")
    return wrapped


def admin_required_for_method(
    method: Callable[..., Awaitable[web.StreamResponse]],
) -> Callable[..., Awaitable[web.StreamResponse]]:
    """Decorator for class methods that require admin authentication."""

    @functools.wraps(method)
    async def wrapped(
        self: Any, request: web.Request, *args: Any, **kwargs: Any
    ) -> web.StreamResponse:
        if request.get("is_authorized", False) and request.get("is_admin", False):
            return await method(self, request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "admin")
    return wrapped


def superadmin_required(handler: Handler) -> Handler:
    @functools.wraps(handler)
    async def wrapped(request: web.Request, *args: Any, **kwargs: Any) -> web.StreamResponse:
        if request.get("is_authorized", False) and request.get("is_superadmin", False):
            return await handler(request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "superadmin")
    return wrapped


def superadmin_required_for_method(
    method: Callable[..., Awaitable[web.StreamResponse]],
) -> Callable[..., Awaitable[web.StreamResponse]]:
    """Decorator for class methods that require superadmin authentication."""

    @functools.wraps(method)
    async def wrapped(
        self: Any, request: web.Request, *args: Any, **kwargs: Any
    ) -> web.StreamResponse:
        if request.get("is_authorized", False) and request.get("is_superadmin", False):
            return await method(self, request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "superadmin")
    return wrapped
